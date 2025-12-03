"""
Document Query API Router.

Endpoints for semantic search and retrieval.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import (
    BaseModel,
)

from internal.infrastructure.container import (
    get_embedding_service,
    get_vector_store_service,
)
from internal.usecases import (
    RetrieveUseCase,
)
from settings.logging import (
    get_logger,
)

logger = get_logger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for semantic search."""

    query: str
    top_k: int = 5
    filter: Optional[
        Dict[
            str,
            Any,
        ]
    ] = None
    namespace: str = "default"
    similarity_threshold: float = 0.0


class QueryResultItem(BaseModel):
    """Single query result."""

    id: str
    text: str
    score: float
    metadata: Dict[
        str,
        Any,
    ]


class QueryResponse(BaseModel):
    """Response model for query."""

    results: List[QueryResultItem]
    query: str
    total_results: int
    namespace: str


class ContextRequest(BaseModel):
    """Request model for context retrieval."""

    query: str
    top_k: int = 5
    filter: Optional[
        Dict[
            str,
            Any,
        ]
    ] = None
    namespace: str = "default"


class ContextResponse(BaseModel):
    """Response model for context retrieval."""

    context: str
    query: str
    chunk_count: int


class StatsResponse(BaseModel):
    """Response model for index stats."""

    index_name: str
    dimension: Optional[int]
    total_vector_count: int
    namespaces: Dict[
        str,
        Any,
    ]


def get_retrieve_usecase() -> RetrieveUseCase:
    """Get retrieve use case with dependencies."""
    return RetrieveUseCase(
        vector_store=get_vector_store_service(),
        embedding_service=get_embedding_service(),
    )


@router.post(
    "/query",
    response_model=QueryResponse,
)
async def query_documents(
    request: QueryRequest,
):
    """
    Semantic search for relevant documents.

    Returns ranked results with scores and metadata.
    Use this for detailed results with individual chunks.
    """
    logger.info(
        "Query request",
        query=request.query[:50],
        top_k=request.top_k,
        namespace=request.namespace,
    )

    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty",
        )

    usecase = get_retrieve_usecase()

    response = await usecase.retrieve(
        query=request.query,
        top_k=request.top_k,
        metadata_filter=request.filter,
        namespace=request.namespace,
        similarity_threshold=request.similarity_threshold,
    )

    return QueryResponse(
        results=[
            QueryResultItem(
                id=r.id,
                text=r.text,
                score=r.score,
                metadata=r.metadata,
            )
            for r in response.results
        ],
        query=response.query,
        total_results=response.total_results,
        namespace=response.namespace,
    )


@router.post(
    "/context",
    response_model=ContextResponse,
)
async def get_context(
    request: ContextRequest,
):
    """
    Get combined context for LLM prompt.

    Returns a single string with all relevant chunks combined,
    ready to be injected into an LLM prompt for RAG.
    """
    logger.info(
        "Context request",
        query=request.query[:50],
        top_k=request.top_k,
    )

    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty",
        )

    usecase = get_retrieve_usecase()

    response = await usecase.retrieve(
        query=request.query,
        top_k=request.top_k,
        metadata_filter=request.filter,
        namespace=request.namespace,
    )

    context = response.get_context_text(separator="\n\n---\n\n")

    return ContextResponse(
        context=context,
        query=request.query,
        chunk_count=response.total_results,
    )


@router.get(
    "/stats",
    response_model=StatsResponse,
)
async def get_index_stats():
    """
    Get vector index statistics.

    Returns information about the Pinecone index including
    vector count and namespace details.
    """
    vector_store = get_vector_store_service()
    stats = await vector_store.get_index_stats()

    return StatsResponse(
        index_name=stats.get(
            "index_name",
            "",
        ),
        dimension=stats.get("dimension"),
        total_vector_count=stats.get(
            "total_vector_count",
            0,
        ),
        namespaces=stats.get(
            "namespaces",
            {},
        ),
    )
