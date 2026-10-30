
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.answer_service import generate_answer

router = APIRouter(prefix="/ask", tags=["RAG"])


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)
    document_id: str | None = None
    document_ids: list[str] = Field(default_factory=list, max_length=100)
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
    )


@router.post("/")
def ask_question(request: AskRequest):
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        history = [
            message.model_dump()
            for message in request.conversation_history
        ]

        document_ids = list(dict.fromkeys(
            document_id
            for document_id in request.document_ids
            if document_id and document_id.strip()
        ))

        return generate_answer(
            query=request.query.strip(),
            top_k=request.top_k,
            document_id=request.document_id,
            document_ids=document_ids,
            conversation_history=history,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
