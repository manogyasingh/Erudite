from .llm_caller import completion, text_completion, structured_completion, StructuredRequest, CompletionRequest
from fastapi import APIRouter
import os

router = APIRouter()

# Load prompts
with open(os.path.join(os.path.dirname(__file__), "../prompts/query_expander_with_context.txt")) as f:
    query_expander_with_context_prompt = f.read()

with open(os.path.join(os.path.dirname(__file__), "../prompts/query_expander.txt")) as f:
    query_expander_prompt = f.read()

with open(os.path.join(os.path.dirname(__file__), "../prompts/topic_generator.txt")) as f:
    topic_generator_prompt = f.read()

with open(os.path.join(os.path.dirname(__file__), "../prompts/article_generator.txt")) as f:
    article_generator_prompt = f.read()

@router.post("/query_expander_with_context")
def query_expander_with_context(model: str, temperature: float, key_phrases: list[str], chunks: list[str]):
    prompt = query_expander_with_context_prompt.replace("{{QUERY}}", "\n\n".join(key_phrases))
    prompt = prompt.replace("{{CHUNKS}}", "\n\n".join(chunks))

    return structured_completion(StructuredRequest(
        model=model,
        text=prompt,
        temperature=temperature,
        schema={
            "expansions": {"type": "array", "items": {"type": "string"}}
        }
    ))

@router.post("/query_expander")
def query_expander(model: str, temperature: float, key_phrases: list[str]):
    prompt = query_expander_prompt.replace("{{QUERY}}", "\n\n".join(key_phrases))

    return structured_completion(StructuredRequest(
        model=model,
        text=prompt,
        temperature=temperature,
        schema={
            "expansions": {"type": "array", "items": {"type": "string"}}
        }
    ))

@router.post("/topic_generator")
def topic_generator(model: str, temperature: float, key_phrases: list[str]):
    prompt = topic_generator_prompt.replace("{{TOPIC}}", "\n\n".join(key_phrases))
    return structured_completion(StructuredRequest(
        model=model,
        text=prompt,
        temperature=temperature,
        schema={
            "knowledge_graph_name": {"type": "string"},
            "subtopics": {"type": "array", "items": {"type": "string"}}
        }
    ))

@router.post("/article_generator")
def article_generator(model: str, temperature: float, topic: str, chunks: list[dict], related_topics: list[str] = []):
    """
    Generate an article about a topic using provided source chunks.
    
    Args:
        model: The LLM model to use
        temperature: Temperature for generation
        topic: The topic to write about
        chunks: List of dicts with keys: 'content', 'source_id', 'metadata'
    """
    # Format chunks with source IDs
    formatted_chunks = []

    for i, chunk in enumerate(chunks):
        source_id = chunk.get('source_id', f'S{i+1}')
        formatted_chunks.append(f"[{source_id}] {chunk['content']}")
    
    prompt = article_generator_prompt.replace("{{TOPIC}}", topic)
    prompt = prompt.replace("{{CHUNKS}}", "\n\n".join(formatted_chunks))
    prompt = prompt.replace("{{RELATED_TOPICS}}", "\n\n".join(related_topics))

    return text_completion(CompletionRequest(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=7999
    ))