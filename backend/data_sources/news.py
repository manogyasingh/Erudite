from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import requests
from newspaper import Article
import concurrent.futures
from datetime import datetime, timedelta
from utils.text_chunking import TextChunker, ChunkingStrategy, RAGDocument
from utils.timing import timing_decorator

router = APIRouter()

# Load environment variables
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY")

class NewsSearchQuery(BaseModel):
    keywords: List[str]
    max_results: int = 10
    chunk_size: int = 3000
    chunk_overlap: int = 200
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    language: Optional[str] = None
    days_back: Optional[int] = 7

# @timing_decorator("Searching News API")
def search_news(query: str, max_results: int, language: Optional[str] = None, days_back: int = 7) -> List[dict]:
    """Search for news articles using NewsAPI."""
    try:
        url = "https://newsapi.org/v2/everything"
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "q": query,
            "apiKey": NEWSAPI_API_KEY,
            "pageSize": max_results,
            "language": "en",
            "sortBy": "relevancy"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get("articles", [])
    except Exception as e:
        print(f"Error in news search: {str(e)}")
        return []

# @timing_decorator("Extracting Article Content")
def extract_article_content(url: str) -> Optional[str]:
    """Extract article content using newspaper3k."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Error extracting content from {url}: {str(e)}")
        return None

# @timing_decorator("Processing Single News Article")
def process_news_article(article: dict, chunker: TextChunker) -> List[RAGDocument]:
    """Process a single news article into RAG documents."""
    try:
        # Extract content
        content = extract_article_content(article["url"])
        if not content:
            return []
            
        # Create base metadata
        metadata = {
            "source": "news",
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "author": article.get("author", ""),
            "source_name": article.get("source", {}).get("name", ""),
            "published_at": article.get("publishedAt", ""),
            "source_database": "newsapi"
        }
        
        # Create documents
        documents = []
        
        # Create summary document
        summary_content = f"Title: {article.get('title')}\n\n"
        if article.get("description"):
            summary_content += f"Description: {article.get('description')}"
            
        summary_metadata = {
            **metadata,
            "chunk_type": "summary",
            "is_full_text": False
        }
        
        documents.append(RAGDocument(
            content=summary_content.strip(),
            metadata=summary_metadata
        ))
        
        # Create content chunks
        content_metadata = {
            **metadata,
            "chunk_type": "content",
            "is_full_text": True
        }
        content_docs = chunker.create_documents(content, content_metadata)
        documents.extend(content_docs)
        
        return documents
        
    except Exception as e:
        print(f"Error processing news article {article.get('url')}: {str(e)}")
        return []

@router.post("/search")
@timing_decorator("News Search Endpoint")
def search_articles(query: NewsSearchQuery):
    """Search news articles and return RAG-ready documents."""
    try:
        # Initialize text chunker
        chunker = TextChunker(
            chunk_size=query.chunk_size,
            chunk_overlap=query.chunk_overlap,
            strategy=query.chunking_strategy
        )
        
        # Search news articles
        search_query = " ".join(query.keywords)
        articles = search_news(
            search_query,
            query.max_results,
            query.language,
            query.days_back
        )
        
        # Process articles into RAG documents in parallel
        all_documents = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(articles)) as executor:
            future_to_article = {
                executor.submit(process_news_article, article, chunker): article
                for article in articles
            }
            
            for future in concurrent.futures.as_completed(future_to_article):
                try:
                    documents = future.result()
                    all_documents.extend(documents)
                except Exception as e:
                    print(f"Error processing news article into documents: {str(e)}")
        
        return {
            "documents": [doc.dict() for doc in all_documents],
            "total_chunks": len(all_documents),
            "total_results": len(articles)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
