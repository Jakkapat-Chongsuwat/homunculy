FROM python:3.12-slim-bookworm
LABEL project=py-clean-arch

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY ./pyproject.toml ./poetry.lock /
RUN pip install --upgrade pip \
	&& pip install --root-user-action=ignore "poetry>=2.1,<2.2" \
	&& poetry config virtualenvs.create false \
	&& poetry install --no-interaction --no-ansi --no-cache --only main,db -vv \
	&& rm -f pyproject.toml poetry.lock

COPY ./src /app/
WORKDIR /app
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
