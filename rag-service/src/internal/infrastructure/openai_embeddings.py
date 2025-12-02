"""
OpenAI Embedding Service Implementation.

Generates text embeddings using OpenAI's embedding models.
"""

from typing import (
    List,
)

from openai import (
    AsyncOpenAI,
)

from internal.domain.services import (
    EmbeddingService,
)
from settings import (
    embedding_settings,
)
from settings.logging import (
    get_logger,
)

logger = get_logger(__name__)


class OpenAIEmbeddingService(EmbeddingService):
    """
    OpenAI embedding service implementation.

    Uses text-embedding-3-small by default (1536 dimensions).
    """

    def __init__(
        self,
    ) -> None:
        """Initialize OpenAI client."""
        self._client = AsyncOpenAI(api_key=embedding_settings.openai_api_key)
        self._model = embedding_settings.model
        self._dimension = embedding_settings.dimension
        self._batch_size = embedding_settings.batch_size

        logger.info(
            "OpenAI Embedding Service initialized",
            model=self._model,
            dimension=self._dimension,
        )

    async def embed_text(
        self,
        text: str,
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dimensions)
        """
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )

        embedding = response.data[0].embedding

        logger.debug(
            "Generated embedding",
            text_length=len(text),
            embedding_dimension=len(embedding),
        )

        return embedding

    async def embed_batch(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        logger.info(
            "Generating batch embeddings",
            count=len(texts),
        )

        all_embeddings = []

        # Process in batches
        for i in range(
            0,
            len(texts),
            self._batch_size,
        ):
            batch = texts[i : i + self._batch_size]

            response = await self._client.embeddings.create(
                model=self._model,
                input=batch,
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            logger.debug(
                "Processed embedding batch",
                batch_start=i,
                batch_size=len(batch),
            )

        logger.info(
            "Batch embedding complete",
            total=len(all_embeddings),
        )
        return all_embeddings

    @property
    def dimension(
        self,
    ) -> int:
        """Get embedding dimension."""
        return self._dimension

    @property
    def model_name(
        self,
    ) -> str:
        """Get model name."""
        return self._model
