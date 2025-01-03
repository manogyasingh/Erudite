from hmac import new
from fastapi import APIRouter
from data_sources.all_retriever import search_all, search_vector_stores, VectorSearchQuery, UniversalSearchQuery
from llm.llm_utils import topic_generator, query_expander, article_generator
import concurrent.futures
import json
import os
import requests
from typing import Dict, List, Any

router = APIRouter()



def update_knowledge_graph_status(uuid: str, status: str):
    requests.put(
        f"http://localhost:8000/knowledge-graphs/status/{uuid}/{status}"
    )
    print(f"Updated status for knowledge graph: {uuid} to {status}")

#@router.post("/generate-article-for-topic")
def generate_article_for_topic(model: str, topic: str, chunks: Dict[str, Any], uuid: str, available_topics: List[str]) -> Dict[str, Any]:
    """Generate an article for a topic using relevant chunks from vector stores."""
    # First expand the query to get better search coverage
    # expanded_queries = query_expander(
    #     model="claude-3-5-haiku-20241022",
    #     temperature=0.7,
    #     key_phrases=[topic]
    # )["expansions"]
    
    # Search vector stores with expanded queries
    chunks_unwrapped = [] 
    for src in chunks.keys():
        print("SOURCE", src)
        chunklist = chunks[src]
        chunks_unwrapped.extend(chunklist)
    
    # Generate article using chunks
    article = article_generator(
        model="openrouter/anthropic/claude-3.5-sonnet:beta",
        temperature=0.4,
        topic=topic,
        chunks=[{
            'content': chunk,
            'chunk_id': i
        } for (i, chunk) in enumerate(chunks_unwrapped)],
        related_topics=available_topics
    )
    
    print("Generated Article", topic)
    return article, [{
            'content': chunk,
            'chunk_id': i
        } for (i, chunk) in enumerate(chunks_unwrapped)]

#@router.post("/generate-knowledge-graph")
def generate_knowledge_graph(query: List[str] ):
    """Generate a knowledge graph for a given query."""
    model = "claude-3-5-haiku-20241022"
    uuid = "wejfnewkf"
    
    topics = query

    # Search for each topic in parallel
    search_results = {}
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(
                search_all,
                UniversalSearchQuery(
                    keywords=[topic],
                    batch_uuid=uuid,
                    max_results_per_source=10
                )
            ): topic for topic in topics
        }
        for future in concurrent.futures.as_completed(futures):
            topic = futures[future]
            try:
                result = future.result()
                search_results[topic] = result
            except Exception as exc:
                print(f"An error occurred while searching for topic '{topic}': {exc}")


    # Generate articles for each topic
    articles = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_topic = {executor.submit(
            generate_article_for_topic,
            model,
            topic,
            search_results[topic],
            uuid,
            prev_nodes  # To create links with previous nodes
        ): topic for topic in topics}
        
        for future in concurrent.futures.as_completed(future_to_topic):
            topic = future_to_topic[future]
            try:
                article, chunks = future.result()
                articles[topic] = {"article": article, "chunks": chunks}
            except Exception as exc:
                print(f"An exception occurred while processing topic {topic}: {exc}")
    

    # Create graph structure
    graph = {
        "nodes": [],
        "links": []
    }

    # Add topic nodes
    for topic in topics:
        article = articles[topic]
        graph["nodes"].append({
            "id": article["title"],
            "name": article["title"],
            "content": article["content"],
            "chunks": article["sources_used"]
        })
    
    
    return graph

@router.post("/update-knowledge-graph")
def update_knowledge_graph( query: List[str]):
    return generate_knowledge_graph(query)

