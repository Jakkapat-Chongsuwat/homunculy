# Waifu Feature Design

## Overview
Waifu AI companion with personality, relationships, and interactions.

## Architecture

```mermaid
graph TD
    subgraph "Entities"
        W[Waifu Model<br/>personality, appearance, stats]
        R[Relationship Model<br/>level, affection, history]
    end

    subgraph "Use Cases"
        WC[Waifu Chat<br/>contextual responses]
        WI[Waifu Interactions<br/>gifts, dates, events]
        WR[Relationship Management<br/>affection, progression]
        WS[WebSocket Chat<br/>real-time messaging]
    end

    subgraph "Controllers"
        WAPI[Waifu REST API<br/>/waifus/*]
        WGraphQL[Waifu GraphQL<br/>waifu mutations/queries]
        WWS[WebSocket Controller<br/>controllers/websocket/]
    end

    subgraph "Repositories"
        WRepo[Waifu Repository<br/>CRUD + AI integration]
    end

    WC --> W
    WI --> R
    WR --> R
    WS --> W
    WS --> R
    WAPI --> WC
    WAPI --> WI
    WAPI --> WR
    WGraphQL --> WC
    WGraphQL --> WI
    WGraphQL --> WR
    WWS --> WS
    WC --> WRepo
    WI --> WRepo
    WR --> WRepo
    WS --> WRepo
```

## Data Models

```mermaid
classDiagram
    class Waifu {
        +id: UUID
        +name: str
        +personality: dict
        +appearance: dict
        +stats: dict
        +created_at: datetime
    }

    class Relationship {
        +user_id: UUID
        +waifu_id: UUID
        +level: int
        +affection: int
        +events: list
        +last_interaction: datetime
    }

    class Interaction {
        +type: str
        +content: str
        +timestamp: datetime
        +affection_change: int
    }

    Waifu ||--o{ Relationship : has
    Relationship ||--o{ Interaction : contains
```

## API Endpoints

### REST API
```mermaid
sequenceDiagram
    participant User
    participant API
    participant UseCase
    participant Repo
    participant AI

    User->>API: POST /waifus/chat
    API->>UseCase: Process chat
    UseCase->>Repo: Get waifu context
    Repo-->>UseCase: Waifu data
    UseCase->>AI: Generate response
    AI-->>UseCase: AI response
    UseCase->>Repo: Update relationship
    UseCase-->>API: Response
    API-->>User: Waifu reply
```

### WebSocket Real-time Chat
```mermaid
sequenceDiagram
    participant Client
    participant WS
    participant UseCase
    participant Repo
    participant AI

    Client->>WS: Connect /ws/agents/{waifu_id}/chat
    WS->>WS: Authenticate & initialize session
    WS-->>Client: Connected

    loop Real-time chat
        Client->>WS: Send message
        WS->>UseCase: Process message
        UseCase->>Repo: Get context & history
        Repo-->>UseCase: Context data
        UseCase->>AI: Generate response
        AI-->>UseCase: AI response
        UseCase->>Repo: Store conversation
        UseCase-->>WS: Formatted response
        WS-->>Client: Stream response
    end

    Client->>WS: Disconnect
    WS->>WS: Cleanup session
```

## Key Features
- Personality-driven responses
- Relationship progression
- Event system
- **Real-time WebSocket chat**
- **Streaming AI responses**
- Integration with existing AI agent framework
- Minimal overhead on current architecture

## Implementation Notes
- Extend existing AI agent models
- Reuse repository patterns
- Add waifu-specific use cases
- **Implement WebSocket endpoints in controllers/websocket/**
- **Add connection management for real-time chat**
- Maintain clean separation</content>
<parameter name="filePath">e:\Personal\Learning\Homunculy\homunculy\docs\waifu-feature-design.md