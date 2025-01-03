from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import requests
import concurrent.futures
from datetime import datetime
import tempfile
import fitz  # PyMuPDF
from utils.text_chunking import TextChunker, ChunkingStrategy, RAGDocument
import arxiv
from tenacity import retry, stop_after_attempt, wait_exponential

# Initialize router
router = APIRouter()

# Load environment variables
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

# API endpoints
SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"

class PaperSearchQuery(BaseModel):
    keywords: List[str]
    max_results: int = 10
    chunk_size: int = 3000
    chunk_overlap: int = 200
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    venue: Optional[str] = None
    fields_of_study: Optional[List[str]] = None
    attempt_full_text: bool = True

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def search_papers_bulk(query: str, max_results: int = 10) -> List[dict]:
    """Search and fetch paper details in bulk using Semantic Scholar API."""
    headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if SEMANTIC_SCHOLAR_API_KEY else {}
    
    response = requests.get(
        f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/search",
        headers=headers,
        params={
            "query": query,
            "limit": max_results,
            "fields": "title,abstract,year,venue,authors,citations,references,fieldsOfStudy,url,openAccessPdf,tldr"
        }
    ) 
    response.raise_for_status()
    return response.json().get("data", [])

def extract_text_from_pdf(pdf_url: str) -> Optional[str]:
    """Extract text from PDF URL."""
    try:
        # Download PDF to temporary file
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            temp_file.write(response.content)
            temp_file.flush()
            
            # Extract text using PyMuPDF
            doc = fitz.open(temp_file.name)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            return text
    except Exception as e:
        print(f"Error extracting PDF text: {str(e)}")
        return None

def get_paper_full_text(paper_info: dict) -> Optional[str]:
    """Try multiple methods to get full paper text."""
    # Method 1: Direct PDF from Semantic Scholar
    if paper_info.get("openAccessPdf"):
        text = extract_text_from_pdf(paper_info["openAccessPdf"]["url"])
        if text:
            return text
    
    # Method 2: Try arXiv
    try:
        if "arxiv" in paper_info.get("url", "").lower():
            arxiv_id = paper_info["url"].split("/")[-1]
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(search.results())
            paper.download_pdf(dirpath=tempfile.gettempdir())
            pdf_path = os.path.join(tempfile.gettempdir(), f"{arxiv_id}.pdf")
            
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            os.remove(pdf_path)
            if text:
                return text
    except Exception as e:
        print(f"Error getting arXiv paper: {str(e)}")
    
    # Fallback: Try TLDR or abstract
    if paper_info.get("tldr"):
        return paper_info["tldr"].get("text", paper_info.get("abstract"))
    return paper_info.get("abstract")

def process_paper(paper_info: dict, chunker: TextChunker, attempt_full_text: bool) -> List[RAGDocument]:
    """Process a single paper into RAG documents."""
    try:
        # Create base metadata
        metadata = {
            "source": "semantic_scholar",
            "paper_id": paper_info["paperId"],
            "title": paper_info["title"],
            "authors": [author["name"] for author in paper_info.get("authors", [])],
            "year": paper_info.get("year"),
            "venue": paper_info.get("venue"),
            "url": paper_info.get("url"),
            "fields_of_study": paper_info.get("fieldsOfStudy", []),
            "citation_count": len(paper_info.get("citations", [])),
            "reference_count": len(paper_info.get("references", [])),
            "source_database": "semantic_scholar",
            "tldr": paper_info.get("tldr", {}).get("text") if paper_info.get("tldr") else None
        }
        
        documents = []
        
        # Create summary document
        summary_content = f"Title: {paper_info['title']}\n\n"
        if paper_info.get("abstract"):
            summary_content += f"Abstract: {paper_info['abstract']}\n\n"
        if paper_info.get("tldr"):
            summary_content += f"TL;DR: {paper_info['tldr']['text']}"
            
        summary_metadata = {
            **metadata,
            "chunk_type": "summary",
            "is_full_text": False
        }
        
        documents.append(RAGDocument(
            content=summary_content.strip(),
            metadata=summary_metadata
        ))
        
        # Process full text if requested
        if attempt_full_text:
            paper_text = get_paper_full_text(paper_info)
            if paper_text and paper_text != paper_info.get("abstract"):
                content_metadata = {
                    **metadata,
                    "chunk_type": "content",
                    "is_full_text": True
                }
                # Create content chunks
                content_docs = chunker.create_documents(paper_text, content_metadata)
                documents.extend(content_docs)
        
        return documents
        
    except Exception as e:
        print(f"Error processing paper {paper_info.get('paperId')}: {str(e)}")
        return []

@router.post("/search")
def search_papers(query: PaperSearchQuery):
    """Search for academic papers and return RAG-ready documents."""
    try:
        # Initialize text chunker
        chunker = TextChunker(
            chunk_size=query.chunk_size,
            chunk_overlap=query.chunk_overlap,
            strategy=query.chunking_strategy
        )
        
        # Search papers with bulk API
        search_query = " ".join(query.keywords)
        papers = search_papers_bulk(search_query, query.max_results)

        filtered_papers = papers    
        
        # Process papers into RAG documents in parallel
        all_documents = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(papers)) as executor:
            future_to_paper = {
                executor.submit(process_paper, paper, chunker, query.attempt_full_text): paper
                for paper in filtered_papers
            }
            
            for future in concurrent.futures.as_completed(future_to_paper):
                try:
                    documents = future.result()
                    all_documents.extend(documents)
                except Exception as e:  
                    print(f"Error processing paper into documents: {str(e)}")
        
        return {
            "documents": [doc.dict() for doc in all_documents],
            "total_chunks": len(all_documents),
            "total_results": len(papers)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
