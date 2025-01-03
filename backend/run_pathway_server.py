"""
Standalone Pathway vector store server.
"""
import os
import pathway as pw
from pathway.xpacks.llm.embedders import SentenceTransformerEmbedder
from pathway.xpacks.llm.vector_store import VectorStoreServer
import torch
from typing import Dict

# Load environment variables
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Alibaba-NLP/gte-large-en-v1.5")
PATHWAY_HOST = os.getenv("PATHWAY_HOST", "0.0.0.0")
PATHWAY_PORT = int(os.getenv("PATHWAY_PORT", 8101))

# Storage configuration
DATA_DIR = os.getenv("RAG_DATA_DIR", os.path.join(os.path.dirname(__file__), "data/rag"))
DOCS_DIR = os.path.join(DATA_DIR, "documents")

class CustomParser(pw.UDF):
    """
    Decode text encoded as UTF-8.
    """

    def __wrapped__(self, contents: bytes) -> list[tuple[str, dict]]:
        docs: list[tuple[str, dict]] = [(contents, {})]
        return docs

    def __call__(self, contents: pw.ColumnExpression, **kwargs) -> pw.ColumnExpression:
        """
        Parse the given document.

        Args:
            - contents: document contents

        Returns:
            A column with a list of pairs for each query. Each pair is a text chunk and
            associated metadata. The metadata is an empty dictionary.
        """
        return super().__call__(contents, **kwargs)

def run_server():
    """Initialize and run the Pathway vector store server."""
    # Initialize embedder
    embedder = SentenceTransformerEmbedder(
        model=EMBEDDING_MODEL,
        device="cuda" if torch.cuda.is_available() else "cpu",
        trust_remote_code=True
    )
    
    # Define schema for documents
    class DocumentSchema(pw.Schema):
        data: str
        _metadata: Dict  # Only uuid and source
    
    # Create input table from documents
    docs_table = pw.io.fs.read(
        DOCS_DIR,
        format="json",
        schema=DocumentSchema,
        mode="streaming",
    )
    
    # Initialize server
    server = VectorStoreServer(docs_table, embedder=embedder, parser=CustomParser())
    
    print(f"Starting Pathway server on {PATHWAY_HOST}:{PATHWAY_PORT}")
    server.run_server(host=PATHWAY_HOST, port=PATHWAY_PORT)

if __name__ == "__main__":
    run_server()

