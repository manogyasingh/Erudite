from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import requests
from newspaper import Article
import concurrent.futures
from utils.text_chunking import TextChunker, ChunkingStrategy, RAGDocument
from utils.timing import timing_decorator

router = APIRouter()

# Load environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

class WebSearchQuery(BaseModel):
    keywords: List[str]
    max_results: int = 10
    chunk_size: int = 3000
    chunk_overlap: int = 200
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    language: Optional[str] = None

# @timing_decorator("Searching Google Custom Search")
def search_google(query: str, max_results: int = 10) -> List[dict]:
    """Search for web pages using Google Custom Search API."""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE_ID,
            "q": query,
            "num": min(max_results, 10)  # Google API limit is 10 per request
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get("items", [])
    except Exception as e:
        print(f"Error in Google search: {str(e)}")
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

# @timing_decorator("Processing Single Web Result")
def process_web_result(result: dict, chunker: TextChunker) -> List[RAGDocument]:
    """Process a single web search result into RAG documents."""
    try:
        # Extract content
        content = extract_article_content(result["link"])
        if not content:
            return []
            
        # Create base metadata
        metadata = {
            "source": "web_search",
            "title": result.get("title", ""),
            "url": result.get("link", ""),
            "snippet": result.get("snippet", ""),
            "source_database": "google_custom_search"
        }
        
        # Create documents
        documents = []
        
        # Create summary document
        summary_content = f"Title: {result.get('title')}\n\n"
        if result.get("snippet"):
            summary_content += f"Snippet: {result.get('snippet')}"
            
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
        print(f"Error processing web result {result.get('link')}: {str(e)}")
        return []

@router.post("/search")
@timing_decorator("Web Search Endpoint")
def search_web(query: WebSearchQuery):
    """Search web pages and return RAG-ready documents."""
    try:
        # Initialize text chunker
        chunker = TextChunker(
            chunk_size=query.chunk_size,
            chunk_overlap=query.chunk_overlap,
            strategy=query.chunking_strategy
        )
        
        # Search web pages
        search_query = " ".join(query.keywords)
        results = search_google(search_query, query.max_results)
        
        # Process results into RAG documents in parallel
        all_documents = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(results)) as executor:
            future_to_result = {
                executor.submit(process_web_result, result, chunker): result
                for result in results
            }
            
            for future in concurrent.futures.as_completed(future_to_result):
                try:
                    documents = future.result()
                    all_documents.extend(documents)
                except Exception as e:
                    print(f"Error processing web result into documents: {str(e)}")
        
        return {
            "documents": [doc.dict() for doc in all_documents],
            "total_chunks": len(all_documents),
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
