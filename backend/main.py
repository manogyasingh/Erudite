import logging
import os
import sqlite3
from contextlib import asynccontextmanager

# Import routers
from auth.router import router as auth_router
from auth.service import get_current_user
from data_sources import router as data_sources_router
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from knowledge_graphs.router import router as knowledge_graphs_router
from llm import router as llm_router
from pipelines import router as pipelines_router

# from agents.orchestrator import router as agents_router

# Load environment variables
load_dotenv()
PROFILE = os.getenv("PROFILE", "DEV")
APP_NAME = os.getenv("APP_NAME", "Knowledge Graph API")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
AUTH_DB_PATH = os.getenv("AUTH_DB_PATH")
KNOWLEDGE_GRAPHS_DB_PATH = os.getenv("KNOWLEDGE_GRAPHS_DB_PATH")

# Configure logging
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def init_database(db_path: str, schema_path: str):
    """Initialize a SQLite database with the given schema"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Initializing {APP_NAME}...")

    # Initialize databases
    init_database(
        AUTH_DB_PATH, os.path.join(os.path.dirname(__file__), "auth/db/schema.sql")
    )
    init_database(
        KNOWLEDGE_GRAPHS_DB_PATH,
        os.path.join(os.path.dirname(__file__), "knowledge_graphs/db/schema.sql"),
    )

    yield

    # Shutdown
    logger.info(f"Shutting down {APP_NAME}...")


# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    description="Backend API for Knowledge Graph Management",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    return {"message": f"{APP_NAME} Backend", "status": "running", "profile": PROFILE}


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include routers based on profile
app.include_router(auth_router)
app.include_router(llm_router)
app.include_router(pipelines_router)
# app.include_router(agents_router)

if PROFILE == "PROD":
    # Protected routes in production
    app.include_router(
        knowledge_graphs_router, dependencies=[Depends(get_current_user)]
    )
    app.include_router(data_sources_router, dependencies=[Depends(get_current_user)])
else:
    # Unprotected routes in development
    app.include_router(knowledge_graphs_router)
    app.include_router(data_sources_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=DEBUG)
