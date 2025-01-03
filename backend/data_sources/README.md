# Project Ligma Data Retrievers

This directory contains the data retrieval components for Project Ligma's RAG system. Each retriever follows a standardized format and contributes to a unified knowledge graph.

## Standard RAG Document Format

All retrievers output documents in the following format:

```python
{
    "content": str,  # The actual text content
    "metadata": {
        "source": str,  # "web", "news", "youtube", "academic", "journals"
        "source_database": str,  # Specific API or database used
        "title": str,
        "url": str,
        "chunk_type": str,  # "summary" or "content"
        "is_full_text": bool,
        ...additional source-specific metadata
    }
}
```

### Source-Specific Metadata

#### Web Search
```python
{
    "source": "web_search",
    "source_database": "google_custom_search",
    "title": str,
    "url": str,
    "snippet": str
}
```

#### News Articles
```python
{
    "source": "news",
    "source_database": "newsapi",
    "title": str,
    "url": str,
    "author": str,
    "source_name": str,
    "published_at": str
}
```

#### YouTube Videos
```python
{
    "source": "youtube",
    "source_database": "youtube_data_api",
    "video_id": str,
    "title": str,
    "channel_title": str,
    "published_at": str,
    "view_count": str,
    "like_count": str,
    "comment_count": str,
    "duration": str,
    "url": str
}
```

#### Academic Papers (Semantic Scholar)
```python
{
    "source": "academic",
    "source_database": "semantic_scholar",
    "title": str,
    "url": str,
    "authors": List[str],
    "year": int,
    "venue": str,
    "fields_of_study": List[str],
    "citation_count": int,
    "reference_count": int,
    "paper_id": str,
    "doi": str,
    "tldr": Optional[str]
}
```

#### Journal Articles (Springer)
```python
{
    "source": "journals",
    "source_database": "springer_nature",
    "article_id": str,
    "title": str,
    "url": str,
    "authors": List[str],
    "publication_name": str,
    "publication_date": str,
    "doi": str,
    "subjects": List[str]
}
```

## Universal Retriever

The `all_retriever.py` provides a unified interface to search across all sources:

1. **Unified Search**: Search across multiple sources in parallel
2. **Vector Storage**: Automatically stores documents in source-specific Pathway vector stores
3. **Semantic Search**: Retrieve documents by semantic similarity using configurable embedding model
4. **UUID Tracking**: Track document batches for filtered retrieval

### Usage Example

```python
# Search across sources
query = UniversalSearchQuery(
    keywords=["quantum computing"],
    max_results_per_source=10,
    sources=["web", "news", "youtube", "academic", "journals"],
    year_start=2020,  # For academic and journal sources
    journal="Nature",  # For journal sources
    subject="Physics"  # For journal sources
)
results = await search_all(query)

# Search vector store
vector_query = VectorSearchQuery(
    query="Latest developments in quantum computing",
    batch_uuid=results["batch_uuid"],  # Optional: filter by batch
    top_k=10
)
similar_docs = await search_vector_stores(vector_query)
```

## Performance Monitoring

All retrievers use the `@timing_decorator` to log:
- Function execution time
- Success/failure status
- Error messages if any

## Error Handling

Each retriever implements:
1. Retries for API calls
2. Graceful fallbacks
3. Detailed error logging
4. Exception propagation to FastAPI endpoints

## Dependencies

Required environment variables:
```
GOOGLE_API_KEY
GOOGLE_SEARCH_ENGINE_ID
YOUTUBE_API_KEY
NEWSAPI_API_KEY
SEMANTIC_SCHOLAR_API_KEY
SPRINGER_API_KEY
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5  # Default if not set
```

Python packages:
```
fastapi
requests
newspaper3k
youtube_transcript_api
pathway
transformers
tenacity
concurrent.futures
