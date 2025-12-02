# RAG Service Makefile

.PHONY: install run dev test lint format docker-build docker-run pinecone-local clean

# Install dependencies
install:
	poetry install

# Run the service
run:
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8001

# Run with hot reload for development
dev:
	poetry run uvicorn src.main:app --reload --port 8001

# Run tests
test:
	poetry run pytest

# Run linter
lint:
	poetry run ruff check src/
	poetry run pyright src/

# Format code
format:
	poetry run black src/
	poetry run ruff check --fix src/

# Build Docker image
docker-build:
	docker build -t rag-service .

# Run Docker container
docker-run:
	docker run -p 8001:8001 --env-file .env rag-service

# Start Pinecone Local for development
pinecone-local:
	docker run -d \
		--name pinecone-local \
		-e PORT=5081 \
		-e INDEX_TYPE=serverless \
		-e DIMENSION=1536 \
		-e METRIC=cosine \
		-p 5081:5081 \
		ghcr.io/pinecone-io/pinecone-index:latest

# Stop Pinecone Local
pinecone-stop:
	docker stop pinecone-local && docker rm pinecone-local

# Clean up
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
