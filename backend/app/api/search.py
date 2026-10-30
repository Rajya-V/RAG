
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.search_service import search_documents

router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)
    document_id: str | None = None


@router.post("/")
def search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    try:
        results = search_documents(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
        )
        return {
            "query": request.query,
            "result_count": len(results),
            "results": results,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
