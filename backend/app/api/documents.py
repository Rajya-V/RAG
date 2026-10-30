
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.services.document_service import MAX_FILE_SIZE
from app.services.ingestion_service import ingest_pdf
from app.services.document_service import DocumentProcessingError

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if not content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="PDF exceeds the 10 MB size limit.",
            )

        # Store the upload temporarily so the ingestion service
        # can process it using the existing file-based interface.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / Path(file.filename).name
            temp_path.write_bytes(content)

            try:
                result = ingest_pdf(temp_path)
            except DocumentProcessingError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=str(exc),
                ) from exc

        return {
            "message": "PDF ingested and stored successfully.",
            "document_id": result["document_id"],
            "filename": result["filename"],
            "page_count": result["page_count"],
            "extracted_page_count": result["extracted_page_count"],
            "chunk_count": result["chunk_count"],
            "stored_chunk_count": result["stored_chunk_count"],
            "chunks": result["chunks"],
        }

    finally:
        await file.close()
