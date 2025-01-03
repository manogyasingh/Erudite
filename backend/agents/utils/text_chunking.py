from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    TokenTextSplitter,
    CharacterTextSplitter,
    Language
)
import tiktoken
import re
from enum import Enum

class ChunkingStrategy(str, Enum):
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    TOKEN = "token"
    MARKDOWN = "markdown"
    YOUTUBE = "youtube"  # Special strategy for YouTube transcripts

class RAGDocument(BaseModel):
    content: str
    metadata: Dict[str, Any]

class TextChunker:
    """Advanced text chunking for RAG applications with multiple strategies."""
    
    def __init__(
        self,
        chunk_size: int = 3000,
        chunk_overlap: int = 200,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        model_name: str = "gpt-3.5-turbo"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        self.model_name = model_name
        
        # Initialize tokenizer for token counting
        self.tokenizer = tiktoken.encoding_for_model(model_name)
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using the model's tokenizer."""
        return len(self.tokenizer.encode(text))
    
    def _create_recursive_splitter(self) -> RecursiveCharacterTextSplitter:
        """Create a recursive splitter that respects semantic boundaries."""
        return RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._count_tokens,
            is_separator_regex=False
        )
    
    def _create_semantic_splitter(self) -> RecursiveCharacterTextSplitter:
        """Create a semantic-aware splitter for code and natural language."""
        return RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,  # Can be customized based on content type
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._count_tokens
        )
    
    def _create_token_splitter(self) -> TokenTextSplitter:
        """Create a token-based splitter using the model's tokenizer."""
        return TokenTextSplitter(
            encoding_name=self.model_name,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    
    def _create_markdown_splitter(self) -> MarkdownHeaderTextSplitter:
        """Create a markdown-aware splitter that respects document structure."""
        headers_to_split_on = [
            ("#", "header_1"),
            ("##", "header_2"),
            ("###", "header_3"),
        ]
        return MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
    
    def _split_youtube_transcript(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Special handling for YouTube transcripts with timestamp metadata."""
        # Extract timestamp-text pairs
        transcript_parts = []
        current_chunk = []
        current_tokens = 0
        current_start_time = None
        
        # Split into lines and process
        lines = text.split('\n')
        for line in lines:
            # Extract timestamp and text
            timestamp_match = re.match(r'\[(\d{2}:\d{2}:\d{2})\] (.*)', line)
            if not timestamp_match:
                continue
                
            timestamp, content = timestamp_match.groups()
            
            # Convert timestamp to seconds for easier processing
            h, m, s = map(int, timestamp.split(':'))
            seconds = h * 3600 + m * 60 + s
            
            # Initialize chunk if needed
            if not current_chunk:
                current_start_time = timestamp
                
            # Add content to current chunk
            current_chunk.append(content)
            current_tokens += self._count_tokens(content)
            
            # Check if chunk is full
            if current_tokens >= self.chunk_size:
                chunk_text = " ".join(current_chunk)
                chunk_metadata = {
                    "timestamp_start": current_start_time,
                    "timestamp_end": timestamp,
                    "start_seconds": seconds
                }
                transcript_parts.append((chunk_text, chunk_metadata))
                
                # Reset for next chunk with overlap
                overlap_tokens = self._count_tokens(" ".join(current_chunk[-2:]))
                if overlap_tokens < self.chunk_overlap:
                    current_chunk = current_chunk[-2:]
                    current_tokens = overlap_tokens
                else:
                    current_chunk = []
                    current_tokens = 0
                
        # Add final chunk if exists
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_metadata = {
                "timestamp_start": current_start_time,
                "timestamp_end": timestamp,
                "start_seconds": seconds
            }
            transcript_parts.append((chunk_text, chunk_metadata))
            
        return transcript_parts
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text before chunking."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove excessive newlines but preserve paragraph breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def _enhance_chunk_metadata(
        self,
        chunks: List[str],
        base_metadata: Dict[str, Any]
    ) -> List[RAGDocument]:
        """Enhance chunk metadata with position and context information."""
        documents = []
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks):
            # Calculate chunk position information
            position_info = {
                "chunk_index": i,
                "total_chunks": total_chunks,
                "is_first_chunk": i == 0,
                "is_last_chunk": i == total_chunks - 1,
            }
            
            # Add token count
            token_info = {
                "token_count": self._count_tokens(chunk)
            }
            
            # Create enhanced metadata
            enhanced_metadata = {
                **base_metadata,
                **position_info,
                **token_info
            }
            
            # Create RAG document
            doc = RAGDocument(
                content=chunk.strip(),
                metadata=enhanced_metadata
            )
            documents.append(doc)
        
        return documents
    
    def create_documents(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[RAGDocument]:
        """Create RAG documents from text using the specified chunking strategy."""
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Skip empty text
        if not text:
            return []
            
        # Handle YouTube transcripts specially
        if self.strategy == ChunkingStrategy.YOUTUBE:
            transcript_parts = self._split_youtube_transcript(text)
            documents = []
            for chunk_text, chunk_metadata in transcript_parts:
                doc = RAGDocument(
                    content=chunk_text,
                    metadata={**metadata, **chunk_metadata}
                )
                documents.append(doc)
            return documents
        
        # Select and apply chunking strategy
        if self.strategy == ChunkingStrategy.RECURSIVE:
            splitter = self._create_recursive_splitter()
            chunks = splitter.split_text(text)
        elif self.strategy == ChunkingStrategy.SEMANTIC:
            splitter = self._create_semantic_splitter()
            chunks = splitter.split_text(text)
        elif self.strategy == ChunkingStrategy.TOKEN:
            splitter = self._create_token_splitter()
            chunks = splitter.split_text(text)
        elif self.strategy == ChunkingStrategy.MARKDOWN:
            splitter = self._create_markdown_splitter()
            chunks = [split.page_content for split in splitter.split_text(text)]
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}")
        
        # Create RAG documents with enhanced metadata
        return self._enhance_chunk_metadata(chunks, metadata)
