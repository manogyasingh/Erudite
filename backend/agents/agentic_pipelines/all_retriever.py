"""
Universal retriever using Pathway with metadata-based source tracking and JSONL storage.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import asyncio
import aiohttp
from datetime import datetime
import os
import uuid
import json
import pathway as pw
from pathway import Table
from pathway.internals import Json, api, parse_graph
from pathway.xpacks.llm.vector_store import VectorStoreClient
from llama_index.core.schema import NodeWithScore, Document
from llama_index.retrievers.pathway import PathwayRetriever
from fastapi import APIRouter, HTTPException
from pathway.xpacks.llm.rerankers import CrossEncoderReranker
import torch
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import pandas as pd

from utils.text_chunking import TextChunker, ChunkingStrategy, RAGDocument
from utils.timing import timing_decorator
import concurrent.futures

router = APIRouter()

# Load environment variables
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-large")
PATHWAY_HOST = os.getenv("PATHWAY_HOST", "localhost")
PATHWAY_PORT = int(os.getenv("PATHWAY_PORT", 8101))

# Storage configuration
DATA_DIR = os.getenv("RAG_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DOCS_DIR = os.path.join(DATA_DIR, "documents")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")

class UnifiedMetadataSchema(pw.Schema):
    """Unified schema for all document types."""
    # Common fields
    uuid: str
    source: str  # web_search, semantic_scholar, youtube, news
    title: str
    url: str
    source_database: str
    chunk_type: str
    is_full_text: bool
    chunk_index: Optional[int]
    total_chunks: Optional[int]
    is_first_chunk: Optional[bool]
    is_last_chunk: Optional[bool]
    token_count: Optional[int]
    
    # Web search specific
    snippet: Optional[str]
    
    # Semantic Scholar specific
    paper_id: Optional[str]
    authors: Optional[List[str]]
    year: Optional[int]
    venue: Optional[str]
    fields_of_study: Optional[List[str]]
    citation_count: Optional[int]
    reference_count: Optional[int]
    tldr: Optional[str]
    
    # YouTube specific
    video_id: Optional[str]
    channel_title: Optional[str]
    published_at: Optional[str]
    view_count: Optional[str]
    like_count: Optional[str]
    comment_count: Optional[str]
    duration: Optional[str]
    
    # News specific
    author: Optional[str]
    source_name: Optional[str]

class SourceConfig:
    """Configuration for each source including weights."""
    def __init__(self, name: str, weight: float = 1.0, recency_boost: float = 1.0):
        self.name = name
        self.weight = weight
        self.recency_boost = recency_boost

class PathwayVectorStore:
    """Advanced retriever using Pathway with JSONL storage."""
    
    def __init__(self):
        """Initialize retriever with unified vector store."""
        self.source_configs = {
            "web_search": SourceConfig("web_search", weight=1.0, recency_boost=1.2),
            "semantic_scholar": SourceConfig("semantic_scholar", weight=1.3, recency_boost=1.0),
            "youtube": SourceConfig("youtube", weight=1.0, recency_boost=1.3),
            "news": SourceConfig("news", weight=1.2, recency_boost=1.5)
        }
        
        # Ensure storage directories exist
        os.makedirs(DOCS_DIR, exist_ok=True)
        os.makedirs(METADATA_DIR, exist_ok=True)
        
        # Initialize metadata table
        self.metadata_table = pw.io.fs.read(
            METADATA_DIR,
            format="json",
            schema=UnifiedMetadataSchema,
            mode="streaming"
        )
        
        # Create indexes
        self.by_uuid = self.metadata_table.groupby(pw.this.uuid)
        self.by_source = self.metadata_table.groupby(pw.this.source)
        self.by_source_db = self.metadata_table.groupby(pw.this.source_database)
        
        # Initialize client and retriever
        self.client = VectorStoreClient(host=PATHWAY_HOST, port=PATHWAY_PORT)
        self.retriever = PathwayRetriever(
            host=PATHWAY_HOST, 
            port=PATHWAY_PORT,
        )

        self.reranker = CrossEncoderReranker(
                model_name=RERANKER_MODEL,
                device="cuda" if torch.cuda.is_available() else "cpu"
            )
    
    def add_documents(self, documents: List[dict], source: str, batch_uuid: str) -> str:
        """Add documents to storage with source tracking."""
        # Create source directories
        source_docs_dir = os.path.join(DOCS_DIR, source)
        source_meta_dir = os.path.join(METADATA_DIR, source)
        os.makedirs(os.path.join(source_docs_dir, f"graph_{batch_uuid}"), exist_ok=True)
        os.makedirs(os.path.join(source_meta_dir, f"graph_{batch_uuid}"), exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        
        # Write documents and metadata
        
        for doc in documents:
            doc_uuid = str(uuid.uuid4())
            docs_path = os.path.join(source_docs_dir, f"graph_{batch_uuid}", doc_uuid + ".jsonl")
            meta_path = os.path.join(source_meta_dir, f"graph_{batch_uuid}", doc_uuid + ".jsonl")
            with open(docs_path, 'w') as doc_file, open(meta_path, 'w') as meta_file:
                
                
                # Create metadata entry
                metadata = {
                    "uuid": doc_uuid,
                    "source": source,
                    "title": doc.get("title", ""),
                    "url": doc.get("url", ""),
                    "source_database": doc.get("source_database", ""),
                    "chunk_type": doc.get("chunk_type", ""),
                    "is_full_text": doc.get("is_full_text", False),
                    "chunk_index": doc.get("chunk_index"),
                    "total_chunks": doc.get("total_chunks"),
                    "is_first_chunk": doc.get("is_first_chunk"),
                    "is_last_chunk": doc.get("is_last_chunk"),
                    "token_count": doc.get("token_count"),
                }
                
                # Add source-specific fields
                if source == "web_search":
                    metadata.update({"snippet": doc.get("snippet")})
                elif source == "semantic_scholar":
                    metadata.update({
                        "paper_id": doc.get("paper_id"),
                        "authors": doc.get("authors"),
                        "year": doc.get("year"),
                        "venue": doc.get("venue"),
                        "fields_of_study": doc.get("fields_of_study"),
                        "citation_count": doc.get("citation_count"),
                        "reference_count": doc.get("reference_count"),
                        "tldr": doc.get("tldr")
                    })
                elif source == "youtube":
                    metadata.update({
                        "video_id": doc.get("video_id"),
                        "channel_title": doc.get("channel_title"),
                        "published_at": doc.get("published_at"),
                        "view_count": doc.get("view_count"),
                        "like_count": doc.get("like_count"),
                        "comment_count": doc.get("comment_count"),
                        "duration": doc.get("duration")
                    })
                elif source == "news":
                    metadata.update({
                        "author": doc.get("author"),
                        "source_name": doc.get("source_name")
                    })
                
                # Write document with minimal metadata
                doc_entry = {
                    "data": doc.get("content", ""),
                    "_metadata": {"uuid": doc_uuid, "source": source}
                }
                doc_file.write(json.dumps(doc_entry) + "\n")
                
                # Write full metadata
                meta_file.write(json.dumps(metadata) + "\n")
        
        return batch_uuid
    
    def search(self, 
    query: str, 
    top_k: int = 10, 
    metadata_filter: str = None,
    ) -> Dict[str, List[Dict]]:
        """Search across all sources with source-specific ranking."""
        if metadata_filter:
            return self.client(query, top_k, metadata_filter)
        return self.client(query, top_k)
    
class UniversalSearchQuery(BaseModel):
    """Universal search parameters across all sources."""
    keywords: List[str]
    batch_uuid: str
    max_results_per_source: int = Field(default=10, gt=0, le=100)
    chunk_size: int = 2000
    chunk_overlap: int = 300
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    language: Optional[str] = "en"
    days_back: Optional[int] = 30
    sources: List[str] = ["web_search", "semantic_scholar", "youtube", "news"]
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    journal: Optional[str] = None
    subject: Optional[str] = None
    apply_source_weights: bool = True
    apply_recency_boost: bool = True

@router.post("/search")
@timing_decorator("Universal Search Endpoint")
def search_all(query: UniversalSearchQuery):
    """Search all specified sources in parallel."""
    batch_uuid = query.batch_uuid
    
    def search_web():
        from .web_search import WebSearchQuery, search_web
        web_query = WebSearchQuery(
            keywords=query.keywords,
            max_results=query.max_results_per_source,
            chunk_size=query.chunk_size,
            chunk_overlap=query.chunk_overlap,
            chunking_strategy=query.chunking_strategy
        )
        return search_web(web_query)
        
    def search_news():
        from .news import NewsSearchQuery, search_articles as search_news
        news_query = NewsSearchQuery(
            keywords=query.keywords,
            max_results=query.max_results_per_source,
            chunk_size=query.chunk_size,
            chunk_overlap=query.chunk_overlap,
            chunking_strategy=query.chunking_strategy
        )
        return search_news(news_query)
        
    def search_youtube():
        from .youtube import YouTubeSearchQuery, search_videos_endpoint
        youtube_query = YouTubeSearchQuery(
            keywords=query.keywords,
            max_results=query.max_results_per_source,
            chunk_size=query.chunk_size,
            chunk_overlap=query.chunk_overlap,
            chunking_strategy=query.chunking_strategy
        )
        return search_videos_endpoint(youtube_query)
        
    def search_academic():
        from .semantic_scholar import PaperSearchQuery, search_papers
        academic_query = PaperSearchQuery(
            keywords=query.keywords,
            max_results=query.max_results_per_source,
            chunk_size=query.chunk_size,
            chunk_overlap=query.chunk_overlap,
            chunking_strategy=query.chunking_strategy
        )
        return search_papers(academic_query)

        
    # Map source names to search functions
    source_functions = {
        "web_search": search_web,
        "news": search_news,
        "youtube": search_youtube,
        "semantic_scholar": search_academic,
    }
    
    # Execute searches in parallel
    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_source = {
            executor.submit(source_functions[source]): source
            for source in query.sources
            if source in source_functions
        }
        
        for future in concurrent.futures.as_completed(future_to_source):
            source = future_to_source[future]
            try:
                result = future.result()
                # print(result)
                documents = result["documents"]
                results[source] = documents
                
                # Add to vector store with source-specific settings
                vector_store.add_documents(documents, source, query.batch_uuid)
                
            except Exception as e:
                print(f"Error searching {source}: {str(e)}")
                results[source] = []


    return results

class VectorSearchQuery(BaseModel):
    """Vector search parameters with source weighting options."""
    query: str
    sources: List[str] = ["web_search", "semantic_scholar", "youtube", "news"]
    batch_uuid: Optional[str] = None
    top_k: int = 10
    rerank: bool = True
    threshold: float = 0.0
    apply_source_weights: bool = True
    apply_recency_boost: bool = True

def table_to_dicts(
    table: Table,
    **kwargs,
) -> tuple[list[api.Pointer], dict[str, dict[api.Pointer, api.Value]]]:
    captured = _compute_tables(table, **kwargs)[0]
    output_data = api.squash_updates(
        captured, terminate_on_error=kwargs.get("terminate_on_error", True)
    )
    keys = list(output_data.keys())
    columns = {
        name: {key: output_data[key][index] for key in keys}
        for index, name in enumerate(table._columns.keys())
    }
    return keys, columns


def table_to_pandas(table: Table, *, include_id: bool = True):
    keys, columns = table_to_dicts(table)
    series_dict = {}
    for name in columns:
        dtype = _dtype_to_pandas(table.schema.typehints()[name])
        if include_id:
            vals: Any = columns[name]
        else:
            # we need to remove keys, otherwise pandas will use them to create index
            vals = columns[name].values()
        series = pd.Series(vals, dtype=dtype)
        series_dict[name] = series
    res = pd.DataFrame(series_dict, index=keys)
    return res


@router.post("/vector_search")
@timing_decorator("Vector Search")
def search_vector_stores(query: VectorSearchQuery):
    """Search vector stores with semantic search, source weights, and recency boost."""
    try:
        filters = [
        ]

        factor = 3 if query.rerank else 1

        if query.batch_uuid:
            filters.append(f"contains(path, `graph_{query.batch_uuid}`)")

        if query.sources:
            or_filters = []
            for source in query.sources:
                or_filters.append(f"contains(path, `{source}`)")
            fil = " || ".join(or_filters)
            filters.append("("+fil+")")

        if len(filters) > 0:
            filterstring = " && ".join(filters)

            results = vector_store.search(
                query=query.query,
                top_k=query.top_k*factor,
                metadata_filter=filterstring
            )
        
        else:
            results = vector_store.search(
                query=query.query,
                top_k=query.top_k*factor
            )
        
        if query.rerank:
            # Convert results to DataFrame for Pathway table
            df = pd.DataFrame({
                "docs": results,
                "prompt": [query.query] * len(results)
            })
            
            # Create Pathway table
            table = pw.debug.table_from_pandas(df)
            
            # Add reranking scores
            table += table.select(
                reranker_scores=vector_store.reranker(
                    pw.this.docs["text"], 
                    pw.this.prompt
                )
            )
            
            # Convert back to Python objects and sort
            reranked_df = table_to_pandas(table)
            
            # Sort by reranker scores
            reranked_df["score"] = pd.to_numeric(reranked_df["reranker_scores"], errors="coerce")
            reranked_df = reranked_df.sort_values("score", ascending=False)
            
            # Update results with new scores and order
            results = reranked_df["docs"].tolist()[:query.top_k]
            scores = reranked_df["score"].tolist()[:query.top_k]
            
            # Update scores in results
            for result, score in zip(results, scores):
                result["score"] = float(score)
        
        return {
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize the vector store
vector_store = PathwayVectorStore()
