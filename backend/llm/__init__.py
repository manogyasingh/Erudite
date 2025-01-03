from fastapi import APIRouter
from .llm_caller import router as caller_router
from .llm_utils import router as utils_router

# Create main router for data sources
router = APIRouter(prefix="/llm", tags=["llm"])

# Include sub-routers
router.include_router(caller_router, prefix="")
router.include_router(utils_router, prefix="/utils")