from fastapi import APIRouter
from .youtube import router as youtube_router
from .news import router as news_router
from .web_search import router as web_search_router
from .semantic_scholar import router as semantic_scholar_router
# from .all_retriever import router as all_router

# Create main router for data sources
router = APIRouter(prefix="/data-sources", tags=["data-sources"])

# Include sub-routers
router.include_router(youtube_router, prefix="/youtube")
router.include_router(news_router, prefix="/news")
router.include_router(web_search_router, prefix="/web-search")
router.include_router(semantic_scholar_router, prefix="/semantic-scholar")
# router.include_router(all_router, prefix="")