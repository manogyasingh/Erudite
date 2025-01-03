from fastapi import APIRouter
from data_sources.all_retriever import search_all, search_vector_stores, VectorSearchQuery, UniversalSearchQuery
from llm.llm_utils import topic_generator, query_expander, article_generator
import concurrent.futures
import json
import os
import requests
from typing import Dict, List, Any
import random
from pydantic import BaseModel

router = APIRouter()

GRAPH_DATA_DIR = os.getenv("GRAPH_DATA_DIR")
API_PATH = os.getenv("API_PATH")

def update_knowledge_graph_status(uuid: str, status: str):
    requests.put(
        f"{API_PATH}/knowledge-graphs/status/{uuid}/{status}"
    )
    print(f"Updated status for knowledge graph: {uuid} to {status}")

def update_knowledge_graph_title(uuid: str, title: str):
    requests.put(
        f"{API_PATH}/knowledge-graphs/title/{uuid}/{title}"
    )
    print(f"Updated title for knowledge graph: {uuid} to {title}")

@router.post("/generate-article-for-topic")
def generate_article_for_topic(model: str, topic: str, chunks: Dict[str, Any], uuid: str, available_topics: List[str]) -> Dict[str, Any]:
    """Generate an article for a topic using relevant chunks from vector stores."""
    # First expand the query to get better search coverage
    # expanded_queries = query_expander(
    #     model="claude-3-5-haiku-20241022",
    #     temperature=0.7,
    #     key_phrases=[topic]
    # )["expansions"]
    
    # Search vector stores with expanded queries
    graphs_dir = os.path.join(GRAPH_DATA_DIR, uuid)
    os.makedirs(graphs_dir, exist_ok=True)

    chunks_unwrapped = [] 
    for src in chunks.keys():
        # print("SOURCE", src)
        chunklist = chunks[src]
        chunks_unwrapped.extend(chunklist)

    model_choice = random.choice([
    "openrouter/google/gemini-pro-1.5-exp",
    "openrouter/google/gemini-pro-1.5",
    "openrouter/google/gemini-pro-1.5",
    "openrouter/anthropic/claude-3.5-haiku-20241022:beta",
    "claude-3-5-haiku-20241022",
    "openrouter/meta-llama/llama-3.2-90b-vision-instruct",
    # "groq/llama-3.2-90b-vision-preview", 
    # "groq/llama-3.1-70b-versatile",
    "openrouter/anthropic/claude-3.5-haiku-20241022:beta",
    "claude-3-5-haiku-20241022",
    "openrouter/meta-llama/llama-3.2-90b-vision-instruct",
    # "groq/llama-3.2-90b-vision-preview", 
    # "groq/llama-3.1-70b-versatile"
    ])

    model_choice = "custom/gemini-flash"
    article = article_generator(
        model=model_choice,
        temperature=0.5,
        topic=topic,
        chunks=[{
            'content': chunk,
            'chunk_id': i
        } for (i, chunk) in enumerate(chunks_unwrapped)],
        related_topics=available_topics
    )
    
    print("GENERATED ARTICLE", topic)
    return article, [{
            'content': chunk,
            'chunk_id': i
        } for (i, chunk) in enumerate(chunks_unwrapped)]

class KnowledgeGraph(BaseModel):
    uuid: str
    query: str

@router.post("/generate-knowledge-graph")
def generate_knowledge_graph(req: KnowledgeGraph):
    print("Recieved pipeline trigger")
    uuid = req.uuid
    query = req.query
    """Generate a knowledge graph for a given query."""
    model = "claude-3-5-haiku-20241022"
    
    # Generate topics
    resp = topic_generator(
        model=model,
        temperature=0.7,
        key_phrases=[query]
    )

    topics = resp["subtopics"]
    graph_name = resp["knowledge_graph_name"]

    print("TOPICS EXPANDED, ", graph_name)
    print(topics)
    
    update_knowledge_graph_title(uuid, graph_name)
    update_knowledge_graph_status(uuid, "topics_found:"+"|".join(topics))

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

    update_knowledge_graph_status(uuid, "search_results_found")

    # Generate articles for each topic
    articles = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_topic = {executor.submit(
            generate_article_for_topic,
            model,
            topic,
            search_results[topic],
            uuid,
            [t for t in topics if t != topic]
        ): topic for topic in topics  if topic in search_results.keys()}
        
        for future in concurrent.futures.as_completed(future_to_topic):
            topic = future_to_topic[future]
            try:
                article, chunks = future.result()
                articles[topic] = {"article": article, "chunks": chunks}
            except Exception as exc:
                print(f"An exception occurred while processing topic {topic}: {exc}")

    print("ARTICLES GENERATED")
    articles["GRAPH_NAME"] = graph_name

    os.makedirs(os.path.join(GRAPH_DATA_DIR, uuid), exist_ok=True)
    
    with open(os.path.join(GRAPH_DATA_DIR, uuid, "articles.json"), "w") as f:
        f.write(json.dumps(articles, indent=2))
    
    update_knowledge_graph_status(uuid, "done")
    
    return {"status": "success", "graph_id": uuid}