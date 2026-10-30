
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.documents import router as documents_router
from app.core.config import settings
from app.api.search import router as search_router
from app.api.ask import router as ask_router
app = FastAPI(
    title=settings.app_name,
    description="A local-first RAG application for enterprise knowledge.",
    version=settings.app_version,
    debug=settings.debug,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(ask_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
    }
