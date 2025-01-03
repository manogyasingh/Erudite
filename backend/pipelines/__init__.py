from fastapi import APIRouter
from .generate_knowledge_graph import router as graph_router

# Create main router for data sources
router = APIRouter(prefix="/pipelines", tags=["pipelines"])

# Include sub-routers
router.include_router(graph_router, prefix="")