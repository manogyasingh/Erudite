import os
from dotenv import load_dotenv
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from .agentic_pipelines.news_agent import search_news, process_news_article, TextChunker
from .agentic_pipelines.semantic_scholar_agent import search_papers_bulk, process_paper
from .agentic_pipelines.youtube_agent import search_videos,process_video
from .agentic_pipelines.web_search_agent import search_google, process_web_result
from .agentic_pipelines.expand_graph import update_knowledge_graph
from .agentic_pipelines.all_retriever import search_vector_stores, VectorSearchQuery
from typing import List, Dict, Any
from utils.text_chunking import ChunkingStrategy, RAGDocument
from fastapi import HTTPException

import time

load_dotenv()  

def fetch_news_articles(keyword: str) -> Dict[str, Any]:
    """
    Fetches news articles, processes them into chunks, and prepares RAG-ready documents.
    
    Args:
        keywords (List[str]): List of keywords for searching news articles.
        max_results (int): Maximum number of articles to fetch.
        chunk_size (int): Size of each text chunk.
        chunk_overlap (int): Overlap between text chunks.
        chunking_strategy (str): Strategy to use for chunking text.
        language (str, optional): Language of the news articles.
        days_back (int): Number of days back to search.

    Returns:
        Dict[str, Any]: Dictionary containing processed RAG documents and metadata.
    """
    max_results: int = 10
    chunk_size: int = 3000
    chunk_overlap: int = 200
    chunking_strategy: str = "recursive",
    language: str = None
    days_back: int = 7

    keywords = [keyword]

    try:
        # Initialize text chunker
        chunker = TextChunker(
            chunk_size=8000,
            chunk_overlap=chunk_overlap,
            strategy=ChunkingStrategy("recursive")
        )
        
        # Search news articles
        search_query = " ".join(keywords)
        articles = search_news(
            query=search_query,
            max_results=6,
            language=language,
            days_back=days_back
        )
        
        # Process articles into RAG documents
        all_documents = []
        for article in articles:
            documents = process_news_article(article, chunker)
            all_documents.extend(documents)
        
        return {
            "documents": [doc.dict() for doc in all_documents],
            "total_chunks": len(all_documents),
            "total_results": len(articles)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing news articles: {str(e)}")

news_retriever_tool = Tool.from_function(
    func=fetch_news_articles,
    name="NewsRetriever",
    description=(
        "Fetches and processes the latest news articles based on keywords. "
        "Returns RAG-ready documents with metadata and text chunks."
    )
)

def fetch_academic_papers(keywords: List[str], max_results: int = 10, chunk_size: int = 3000,
                          chunk_overlap: int = 200,
                          year_start: int = None, year_end: int = None, venue: str = None,
                          fields_of_study: List[str] = None, attempt_full_text: bool = False) -> Dict[str, Any]:
    """
    Fetches academic papers from Semantic Scholar, processes them into chunks, 
    and prepares RAG-ready documents.

    Args:
        keywords (List[str]): List of keywords for searching papers.
        max_results (int): Maximum number of papers to fetch.
        chunk_size (int): Size of each text chunk.
        chunk_overlap (int): Overlap between text chunks.
        chunking_strategy (str): Strategy to use for chunking text.
        year_start (int, optional): Start year for filtering papers.
        year_end (int, optional): End year for filtering papers.
        venue (str, optional): Filter papers by venue.
        fields_of_study (List[str], optional): Filter papers by fields of study.
        attempt_full_text (bool): Whether to fetch and process full text of papers.

    Returns:
        Dict[str, Any]: Dictionary containing processed RAG documents and metadata.
    """
    try:
        # Initialize text chunker
        chunker = TextChunker(
            chunk_size=8000,
            chunk_overlap=chunk_overlap,
            strategy=ChunkingStrategy("recursive")
        )
        
        attempt_full_text = False
        
        # Search for papers using Semantic Scholar API
        search_query = " ".join(keywords)
        papers = search_papers_bulk(query=search_query, max_results=6)

        # Optionally filter papers (e.g., by year or venue)
        filtered_papers = [
            paper for paper in papers
            if (year_start is None or paper.get("year", 0) >= year_start) and
               (year_end is None or paper.get("year", 0) <= year_end) and
               (venue is None or paper.get("venue", "").lower() == venue.lower()) and
               (fields_of_study is None or any(f in paper.get("fieldsOfStudy", []) for f in fields_of_study))
        ]

        # Process papers into RAG documents
        all_documents = []
        for paper in filtered_papers:
            documents = process_paper(paper, chunker, attempt_full_text)
            all_documents.extend(documents)
        
        return {
            "documents": [doc.dict() for doc in all_documents],
            "total_chunks": len(all_documents),
            "total_results": len(filtered_papers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing papers: {str(e)}")

semantic_scholar_tool = Tool.from_function(
    func=fetch_academic_papers,
    name="SemanticScholarRetriever",
    description=(
        "Fetches and processes academic papers from Semantic Scholar. "
        "Supports keyword-based search, filtering by year, venue, and fields of study, "
        "and processes papers into RAG-ready documents with metadata and text chunks."
    )
)

def fetch_youtube_videos(keywords: List[str], max_results: int = 10, chunk_size: int = 3000,
                         chunk_overlap: int = 200, chunking_strategy: str = "recursive",
                         language: str = None, days_back: int = 7) -> Dict[str, Any]:
    """
    Fetches YouTube videos using YouTube Data API, processes transcripts into chunks, 
    and prepares RAG-ready documents.

    Args:
        keywords (List[str]): List of keywords for searching videos.
        max_results (int): Maximum number of videos to fetch.
        chunk_size (int): Size of each text chunk.
        chunk_overlap (int): Overlap between text chunks.
        chunking_strategy (str): Strategy to use for chunking text.
        language (str, optional): Language filter for the video transcripts.
        days_back (int): Number of days back to search for videos.

    Returns:
        Dict[str, Any]: Dictionary containing processed RAG documents and metadata.
    """
    try:
        # Initialize text chunker
        chunker = TextChunker(
            chunk_size=8000,
            chunk_overlap=chunk_overlap,
            strategy=ChunkingStrategy("recursive")
        )
        
        # Search videos using YouTube API
        search_query = " ".join(keywords)
        videos = search_videos(
            query=search_query,
            max_results=4,
            language=language,
            days_back=days_back
        )
        
        # Process videos into RAG documents
        all_documents = []
        for video in videos:
            documents = process_video(video, chunker, language)
            all_documents.extend(documents)
        
        return {
            "documents": [doc.dict() for doc in all_documents],
            "total_chunks": len(all_documents),
            "total_results": len(videos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing YouTube videos: {str(e)}")

youtube_tool = Tool.from_function(
    func=fetch_youtube_videos,
    name="YouTubeVideoRetriever",
    description=(
        "Fetches and processes YouTube videos based on keywords. "
        "Includes transcript processing and prepares RAG-ready documents with metadata and text chunks."
    )
)

def fetch_web_search_results(keywords: List[str], max_results: int = 10, chunk_size: int = 3000,
                             chunk_overlap: int = 200, chunking_strategy: str = "recursive",
                             language: str = None) -> Dict[str, Any]:
    """
    Fetches web search results using Google Custom Search API, processes them into chunks, 
    and prepares RAG-ready documents.

    Args:
        keywords (List[str]): List of keywords for searching web pages.
        max_results (int): Maximum number of web search results to fetch.
        chunk_size (int): Size of each text chunk.
        chunk_overlap (int): Overlap between text chunks.
        chunking_strategy (str): Strategy to use for chunking text.
        language (str, optional): Language filter for the search.

    Returns:
        Dict[str, Any]: Dictionary containing processed RAG documents and metadata.
    """
    try:
        # Initialize text chunker
        chunker = TextChunker(
            chunk_size=8000,
            chunk_overlap=chunk_overlap,
            strategy=ChunkingStrategy("recursive")
        )
        
        # Search web pages using Google Custom Search
        search_query = " ".join(keywords)
        results = search_google(query=search_query, max_results=10)
        
        # Process results into RAG documents
        all_documents = []
        for result in results:
            documents = process_web_result(result, chunker)
            all_documents.extend(documents)
        
        return {
            "documents": [doc.dict() for doc in all_documents],
            "total_chunks": len(all_documents),
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing web search results: {str(e)}")

web_search_tool = Tool.from_function(
    func=fetch_web_search_results,
    name="WebSearchRetriever",
    description=(
        "Fetches and processes web search results from Google Custom Search API. "
        "Returns RAG-ready documents with metadata and text chunks."
    )
)


def update_knowledge_graph_tool(query: List[str]) -> Dict[str, str]:
    """
    Wrapper for the update_knowledge_graph function.

    Args:
        query (List[str]): List of key phrases (nodes) to be added to the graph.

    Returns:
        Dict[str, str]: The status and the new merged graph UUID.
    """
    result = update_knowledge_graph( query)
    return result

graph_expander_tool = Tool.from_function(
    func=update_knowledge_graph_tool,
    name="GraphExpander",
    description=(
        "Expands an existing knowledge graph by adding new nodes based on the given list of key phrases. "
        "Takes a list of key phrases, and returns the status and new graph nodes."
    )
)

def vector_store_search_tool(query: str, sources: List[str] = None, top_k: int = 10) -> Dict[str, Any]:
    """
    Wrapper for the Pathway vector store search.

    Args:
        query (str): The search query.
        sources (List[str], optional): List of sources to search in. Defaults to ["web_search", "semantic_scholar", "youtube", "news"].
        top_k (int, optional): Number of top results to retrieve. Defaults to 10.

    Returns:
        Dict[str, Any]: Search results containing documents and metadata.
    """
    # Default sources if not provided
    sources = sources or ["web_search", "semantic_scholar", "youtube", "news"]
    
    # Prepare query parameters
    search_query = VectorSearchQuery(
        query=query,
        sources=sources,
        top_k=top_k,
        rerank=True,  # Optionally enable reranking
    )
    
    # Call the vector store search function
    results = search_vector_stores(search_query)
    return results

vector_store_tool = Tool.from_function(
    func=vector_store_search_tool,
    name="VectorStoreRetriever",
    description=(
        "Searches a Pathway vector store for documents based on a query. "
        "Supports filtering by sources (e.g., web_search, semantic_scholar, youtube, news) and returns ranked results."
    )
)
