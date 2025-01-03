"""
Base template for converting data source retrievers into LangChain agents.
"""

from langchain.agents import Tool
from langchain.agents.agent import AgentExecutor, BaseMultiActionAgent
from langchain.schema import AgentAction, AgentFinish
from typing import List, Dict, Optional, Any, Union, Tuple
from pydantic import BaseModel, Field
import asyncio
import aiohttp
from datetime import datetime
import os
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.text_chunking import TextChunker, ChunkingStrategy, RAGDocument
from utils.timing import timing_decorator

class RetrieverAgent(BaseMultiActionAgent):
    """Base class for retriever-based agents"""

    api_key: str = "your_default_api_key"
    base_url: str = "your_default_base_url"
    
    def __init__(self, api_key: str, base_url: str):
        super().__init__()
        print(f"RetrieverAgent initialized with API: {api_key}")
        self.api_key = api_key
        self.base_url = base_url

    @property
    def input_keys(self):
        return ["query"]

    def get_tools(self) -> List[Tool]:
        """Get the tools available to this agent"""
        return [
            Tool(
                name="search",
                func=lambda query: asyncio.run(self.search(query)),  # Wrap async call
                description="Search for information using the retriever"
            ),
            Tool(
                name="process_results",
                func=self.process_results,
                description="Process and format the search results"
            )
        ]

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Execute search using the retriever"""
        raise NotImplementedError("Implement search for specific retriever")

    def process_results(self, results: List[Dict[str, Any]]) -> List[RAGDocument]:
        """Process raw results into RAG documents"""
        raise NotImplementedError("Implement result processing for specific retriever")

    def plan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        **kwargs: Any
    ) -> Union[List[AgentAction], AgentFinish]:
        """Plan next actions based on current state"""
        
        query = kwargs.get("query", "")
        
        # If no steps taken, start with search
        if not intermediate_steps:
            return [AgentAction(
                tool="search",
                tool_input=query,
                log="Initiating search with retriever"
            )]
            
        # If search completed, process results
        if len(intermediate_steps) == 1:
            tool_output = intermediate_steps[0][1]  # The output from the search step
            if isinstance(tool_output, str):  # Ensure it's a string or dictionary
                return [AgentAction(
                    tool="process_results",
                    tool_input=tool_output,
                    log="Processing search results"
                )]
            else:
                return AgentFinish(
                    return_values={"output": "Error: Invalid output from search"},
                    log="Invalid search output"
                )
            
        # Return final results
        if len(intermediate_steps) == 2:
            return AgentFinish(
                return_values={"output": intermediate_steps[1][1]},
                log="Search and processing complete"
            )

        return AgentFinish(
            return_values={"output": "Error: Unexpected agent state"},
            log="Agent encountered an error"
        )

    
    async def aplan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        **kwargs: Any
    ) -> Union[List[AgentAction], AgentFinish]:
        """Asynchronous plan for the agent."""
        
        query = kwargs.get("query", "")
        
        # If no steps taken, start with search
        if not intermediate_steps:
            return [AgentAction(
                tool="search",
                tool_input=query,
                log="Initiating search with retriever"
            )]
            
        # If search completed, process results
        if len(intermediate_steps) == 1:
            tool_output = intermediate_steps[0][1]
            if isinstance(tool_output, str):  # Ensure the output is valid
                return [AgentAction(
                    tool="process_results",
                    tool_input=tool_output,
                    log="Processing search results"
                )]
            else:
                return AgentFinish(
                    return_values={"output": "Error: Invalid search output"},
                    log="Invalid search output"
                )
            
        # Return final results
        if len(intermediate_steps) == 2:
            return AgentFinish(
                return_values={"output": intermediate_steps[1][1]},
                log="Search and processing complete"
            )

        return AgentFinish(
            return_values={"output": "Error: Unexpected agent state"},
            log="Agent encountered an error"
        )


def create_retriever_agent(
    agent_class,
    api_key: str,
    base_url: str
) -> AgentExecutor:
    """Create an agent executor for a specific retriever"""
    print(f"Creating {agent_class.__name__} agent")
    print(f"API key: {api_key}")
    agent = agent_class(api_key=api_key, base_url=base_url)
    print("Agent created")
    return AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=agent.get_tools(),
        verbose=True
    )
