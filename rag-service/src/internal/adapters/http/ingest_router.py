"""
Document Ingestion API Router.

Endpoints for uploading and indexing documents.
"""

import json
from io import BytesIO
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader

from internal.infrastructure.container import (
    get_chunking_service,
    get_embedding_service,
    get_vector_store_service,
)
from internal.usecases import IngestUseCase
from settings.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class TextIngestRequest(BaseModel):
    """Request model for text ingestion."""

    text: str
    source: str = "api"
    title: Optional[str] = None
    category: Optional[str] = None
    namespace: str = "default"
    metadata: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    """Response model for ingestion."""

    document_id: str
    chunk_count: int
    vectors_upserted: int
    source: str
    success: bool
    error: Optional[str] = None


def get_ingest_usecase() -> IngestUseCase:
    """Get ingest use case with dependencies."""
    return IngestUseCase(
        vector_store=get_vector_store_service(),
        embedding_service=get_embedding_service(),
        chunking_service=get_chunking_service(),
    )


@router.post(
    "/ingest/text",
    response_model=IngestResponse,
)
async def ingest_text(
    request: TextIngestRequest,
):
    """
    Ingest text content into the vector store.

    This endpoint:
    1. Chunks the text into smaller pieces
    2. Generates embeddings for each chunk
    3. Upserts vectors to Pinecone
    """
    logger.info(
        "Text ingestion request",
        source=request.source,
        text_length=len(request.text),
    )

    usecase = get_ingest_usecase()

    result = await usecase.ingest_text(
        text=request.text,
        source=request.source,
        title=request.title,
        category=request.category,
        namespace=request.namespace,
        custom_metadata=request.metadata,
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error,
        )

    return IngestResponse(**result.to_dict())


@router.post(
    "/ingest",
    response_model=IngestResponse,
)
async def ingest_file(
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
    namespace: str = Form("default"),
):
    """
    Ingest a file into the vector store.

    Supported formats:
    - .txt - Plain text
    - .md - Markdown
    - .pdf - PDF documents

    Metadata should be JSON string: {"category": "docs", "author": "John"}
    """
    logger.info(
        "File ingestion request",
        filename=file.filename,
        content_type=file.content_type,
    )

    # Parse metadata
    try:
        meta_dict = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid metadata JSON",
        ) from exc

    # Read file content
    content = await file.read()

    # Extract text based on file type
    filename = file.filename or "unknown"

    if filename.endswith(".pdf"):
        # Extract text from PDF
        try:
            reader = PdfReader(BytesIO(content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"PDF extraction failed: {e}",
            ) from e
    else:
        # Plain text or markdown
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail="File must be UTF-8 encoded",
            ) from exc

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="File is empty or unreadable",
        )

    # Ingest the text
    usecase = get_ingest_usecase()

    result = await usecase.ingest_text(
        text=text,
        source=filename,
        title=meta_dict.get("title"),
        category=meta_dict.get("category"),
        namespace=namespace,
        custom_metadata=meta_dict,
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error,
        )

    return IngestResponse(**result.to_dict())


@router.delete("/ingest/{namespace}")
async def delete_namespace(
    namespace: str,
):
    """
    Delete all vectors in a namespace.

    ⚠️ This is a destructive operation.
    """
    logger.warning(
        "Delete namespace request",
        namespace=namespace,
    )

    vector_store = get_vector_store_service()
    await vector_store.delete(
        namespace=namespace,
        delete_all=True,
    )

    return {
        "message": f"Namespace '{namespace}' cleared",
        "success": True,
    }
