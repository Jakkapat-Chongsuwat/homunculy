# RAG Service

🔍 **Retrieval-Augmented Generation Service** - Document ingestion pipeline and semantic search with Pinecone.

## Overview

| Aspect | Details |
|--------|---------|
| **Language** | Python 3.12+ |
| **Framework** | FastAPI |
| **Vector DB** | Pinecone (Local for dev, Cloud for prod) |
| **Embeddings** | OpenAI text-embedding-3-small |
| **Architecture** | Clean Architecture |

## Key Features

- 📄 **Document Ingestion** - Upload PDF, Markdown, Text files
- ✂️ **Smart Chunking** - Configurable text splitting with overlap
- 🧠 **Embedding Generation** - OpenAI embeddings for semantic search
- 🔍 **Semantic Search** - Query documents with natural language
- 🐳 **Pinecone Local** - Docker-based development environment

## Data Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Document │───▶│ Chunking │───▶│ Embedding│───▶│ Pinecone │
│  Upload  │    │ (512 tok)│    │ (OpenAI) │    │  Upsert  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## Project Structure

```
rag-service/
├── src/
│   ├── main.py                    # FastAPI entry point
│   ├── settings/                  # Configuration
│   │   ├── config.py
│   │   └── pinecone.py
│   └── internal/
│       ├── domain/                # Entities & interfaces
│       │   ├── entities/
│       │   └── services/
│       ├── usecases/              # Business logic
│       │   ├── ingest.py
│       │   └── retrieve.py
│       ├── adapters/              # HTTP handlers
│       │   └── http/
│       └── infrastructure/        # External services
│           ├── pinecone/
│           └── embeddings/
├── tests/
├── Dockerfile
└── pyproject.toml
```

## Quick Start

### 1. Start Pinecone Local (Docker)

```bash
docker run -d \
  --name pinecone-local \
  -e PORT=5081 \
  -e INDEX_TYPE=serverless \
  -e DIMENSION=1536 \
  -e METRIC=cosine \
  -p 5081:5081 \
  ghcr.io/pinecone-io/pinecone-index:latest
```

### 2. Install & Run

```bash
cd rag-service
poetry install
poetry run uvicorn src.main:app --reload --port 8001
```

### 3. Environment Variables

```env
# Pinecone
PINECONE_ENVIRONMENT=local          # 'local' or 'cloud'
PINECONE_API_KEY=pclocal            # Any value for local
PINECONE_HOST=localhost:5081        # Pinecone Local host
PINECONE_INDEX_NAME=homunculy-rag

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...

# RAG Settings
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=5
```

## API Endpoints

### Ingest Documents

```bash
# Upload a document
curl -X POST http://localhost:8001/api/v1/ingest \
  -F "file=@document.pdf" \
  -F "metadata={\"source\": \"manual\", \"category\": \"docs\"}"

# Ingest text directly
curl -X POST http://localhost:8001/api/v1/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document content here...",
    "metadata": {"source": "api", "title": "My Doc"}
  }'
```

### Query Documents

```bash
curl -X POST http://localhost:8001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the architecture of the system?",
    "top_k": 5,
    "filter": {"category": "docs"}
  }'
```

### Response Format

```json
{
  "results": [
    {
      "id": "doc_chunk_001",
      "text": "The system uses Clean Architecture...",
      "score": 0.92,
      "metadata": {
        "source": "architecture.md",
        "chunk_index": 0
      }
    }
  ],
  "query": "What is the architecture?",
  "total_results": 5
}
```

## Integration with Homunculy Agent

The RAG service exposes a simple API that the Homunculy agent can call:

```python
# In homunculy agent tool
async def retrieve_context(query: str) -> list[str]:
    response = await httpx.post(
        "http://rag-service:8001/api/v1/query",
        json={"query": query, "top_k": 5}
    )
    return [r["text"] for r in response.json()["results"]]
```

## Via Aspire (Recommended)

Run with the full stack:

```bash
cd ../aspire
dotnet run --project Homunculy.AppHost
```

## Testing

```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=src
```
