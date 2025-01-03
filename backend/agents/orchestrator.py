import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_anthropic import ChatAnthropic
from typing import AsyncIterator, Dict
import json

from .tools import news_retriever_tool, semantic_scholar_tool, youtube_tool, web_search_tool, graph_expander_tool, vector_store_tool, fetch_news_articles

load_dotenv()

router = APIRouter(prefix="/agents", tags=["agents"])

class PromptRequest(BaseModel):
    prompt: str

# Load system prompt
with open("prompts/agentic_system_prompt.txt", "r") as file:
    agentic_system_prompt = file.read()

# Initialize LLM and tools
def create_llm(streaming: bool = False):
    return ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        temperature=0.2,
        max_tokens=1000,
        streaming=streaming
    )

tools = [
    fetch_news_articles, 
    semantic_scholar_tool, 
    youtube_tool, 
    web_search_tool, 
    graph_expander_tool, 
    vector_store_tool
]

# Create two agents - one for streaming and one for regular responses
regular_agent = initialize_agent(
    tools=tools,
    llm=create_llm(streaming=False),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    system_message=agentic_system_prompt
)

streaming_agent = initialize_agent(
    tools=tools,
    llm=create_llm(streaming=True),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    system_message=agentic_system_prompt,
    return_intermediate_steps=True
)

@router.post("/invoke")
async def invoke_agent(request: PromptRequest):
    """Non-streaming endpoint that returns the final response"""
    try:
        response = await regular_agent.ainvoke({"input": request.prompt})
        if isinstance(response, dict) and "output" in response:
            return {"response": response["output"]}
        return {"response": str(response)}
    except Exception as e:
        print(f"Agent error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_agent_steps(promptin) -> AsyncIterator[str]:
    """Helper function to format streaming output"""

    async for event in streaming_agent.astream_events(
    {"input": promptin},
    version="v1",
    ):
        kind = event["event"]
        if kind == "on_chain_start":
            if (
                event["name"] == "Agent"
            ):  # Was assigned when creating the agent with `.with_config({"run_name": "Agent"})`
                print    (
                    f"Starting agent: {event['name']} with input: {event['data'].get('input')}"
                )
                yield    (
                    f"Starting agent: {event['name']} with input: {event['data'].get('input')}"
                )
        elif kind == "on_chain_end":
            if (
                event["name"] == "Agent"
            ):  # Was assigned when creating the agent with `.with_config({"run_name": "Agent"})`
                print (
                    f"Done agent: {event['name']} with output: {event['data'].get('output')['output']}"
                )
                yield (
                    f"Done agent: {event['name']} with output: {event['data'].get('output')['output']}"
                )
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
                # Empty content in the context of OpenAI means
                # that the model is asking for a tool to be invoked.
                # So we only print non-empty content
            print ("Content: "+content)
            yield ("Content: "+content)
        elif kind == "on_tool_start":
            print (
                f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}"
            )
            yield (
                f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}"
            )
        elif kind == "on_tool_end":
            print (f"Done tool: {event['name']}")
            print (f"Tool output was: {event['data'].get('output')}")
            yield (f"Done tool: {event['name']}")
            yield (f"Tool output was: {event['data'].get('output')}")



@router.post("/stream")
def stream_agent(request: PromptRequest):
    """Streaming endpoint that returns agent's thought process"""
    try:
        return StreamingResponse(
            stream_agent_steps(request.prompt),
            media_type="text/event-stream"
        )
    except Exception as e:
        print(f"Streaming error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))