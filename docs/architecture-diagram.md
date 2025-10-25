# Project Architecture Diagram

This diagram illustrates the Clean Architecture implementation of the Homunculy project, a Pokémon API built with FastAPI.

```mermaid
graph TD
    %% External Interfaces
    Client[Client<br/>HTTP/GraphQL Request]

    %% Frameworks & Drivers Layer
    subgraph "Frameworks & Drivers"
        FastAPI[FastAPI<br/>main.py]
        DB[Database<br/>settings/db/]
        Docker[Docker<br/>Dockerfile<br/>docker-compose.yml]
    end

    %% Interface Adapters Layer
    subgraph "Interface Adapters"
        REST[REST Controller<br/>controllers/rest/]
        GraphQL[GraphQL Controller<br/>controllers/graphql/]
        RepoAbs[Repository Abstractions<br/>repositories/abstraction/]
        Relational[Relational DB Repo<br/>repositories/relational_db/]
        Document[Document DB Repo<br/>repositories/document_db/]
        KeyValue[Key-Value DB Repo<br/>repositories/key_value_db/]
        LLM[LLM Service Repo<br/>repositories/llm_service/]
        PydanticAI[Pydantic AI Client<br/>repositories/pydantic_ai_client/]
    end

    %% Use Cases Layer
    subgraph "Use Cases"
        PokemonUC[Pokemon Use Cases<br/>usecases/pokemon.py]
        AIAgentUC[AI Agent Use Cases<br/>usecases/ai_agent.py]
    end

    %% Entities Layer
    subgraph "Entities"
        PokemonModel[Pokemon Model<br/>models/pokemon/]
        AIAgentModel[AI Agent Model<br/>models/ai_agent/]
    end

    %% Common & DI
    subgraph "Common & Infrastructure"
        Common[Common Utils<br/>common/]
        DI[Dependency Injection<br/>di/]
        Settings[Settings<br/>settings/]
    end

    %% Flow
    Client --> FastAPI
    FastAPI --> REST
    FastAPI --> GraphQL

    REST --> PokemonUC
    REST --> AIAgentUC
    GraphQL --> PokemonUC
    GraphQL --> AIAgentUC

    PokemonUC --> RepoAbs
    AIAgentUC --> RepoAbs

    RepoAbs --> Relational
    RepoAbs --> Document
    RepoAbs --> KeyValue
    RepoAbs --> LLM
    RepoAbs --> PydanticAI

    Relational --> DB
    Document --> DB
    KeyValue --> DB

    PokemonUC --> PokemonModel
    AIAgentUC --> AIAgentModel

    %% Infrastructure connections
    FastAPI --> DI
    REST --> DI
    GraphQL --> DI
    PokemonUC --> DI
    AIAgentUC --> DI
    RepoAbs --> DI

    DI --> Common
    DI --> Settings

    %% Docker
    Docker -.-> FastAPI
    Docker -.-> DB

    %% Styling
    classDef framework fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef adapter fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef usecase fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef entity fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef infra fill:#fafafa,stroke:#424242,stroke-width:2px

    class FastAPI,DB,Docker framework
    class REST,GraphQL,RepoAbs,Relational,Document,KeyValue,LLM,PydanticAI adapter
    class PokemonUC,AIAgentUC usecase
    class PokemonModel,AIAgentModel entity
    class Common,DI,Settings infra
```

## Architecture Explanation

This project follows **Clean Architecture** principles with the following layers:

### Entities (Domain Layer)
- **Pokemon Model**: Core business entities for Pokémon data
- **AI Agent Model**: Core business entities for AI agent functionality

### Use Cases (Application Layer)
- **Pokemon Use Cases**: Application-specific business rules for Pokémon operations
- **AI Agent Use Cases**: Application-specific business rules for AI agent operations

### Interface Adapters
- **Controllers**: REST and GraphQL endpoints that adapt external requests to internal format
- **Repositories**: Multiple database implementations (Relational, Document, Key-Value) with abstractions for database independence

### Frameworks & Drivers
- **FastAPI**: Web framework handling HTTP requests
- **Database Settings**: Configuration for various database types
- **Docker**: Containerization for deployment

### Infrastructure
- **Dependency Injection**: Manages component dependencies and Unit of Work pattern
- **Common Utils**: Shared utilities and helpers
- **Settings**: Application configuration

## Data Flow Example (POST /pokemons)

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Controller
    participant UseCase
    participant Repository
    participant Database

    Client->>FastAPI: POST /pokemons
    FastAPI->>Controller: Raw Request
    Controller->>Controller: Map to DTO
    Controller->>UseCase: Business Logic
    UseCase->>Repository: Save Entity
    Repository->>Database: Persist Data
    Database-->>Repository: Success
    Repository-->>UseCase: Entity
    UseCase-->>Controller: Response Data
    Controller->>Controller: Map to Response DTO
    Controller-->>FastAPI: HTTP Response
    FastAPI-->>Client: 201 Created
```

## Supported Databases

The project supports multiple database types through different repository implementations:

- **Relational**: SQLite, MySQL, PostgreSQL (SQLAlchemy)
- **Document**: MongoDB
- **Key-Value**: Redis
- **LLM Service**: External AI services
- **Pydantic AI Client**: AI-powered operations

This architecture ensures:
- **Testability**: Each layer can be tested independently
- **Framework Independence**: Core business logic doesn't depend on external frameworks
- **Database Independence**: Business rules work with any database implementation
- **UI Independence**: API interfaces (REST/GraphQL) can be changed without affecting core logic</content>
<parameter name="filePath">e:\Personal\Learning\Homunculy\homunculy\docs\architecture-diagram.md