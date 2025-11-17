# Management Service Database

PostgreSQL database schema for the Management Service, managed with Liquibase.

## Schema Overview

### Tables

#### users
- **Purpose**: Store user accounts with subscription tiers
- **Key Fields**: id (UUID), email (unique), subscription_tier (free/premium/enterprise)
- **Relationships**: 1:1 with quotas, 1:N with agent_assignments and usage_metrics

#### quotas
- **Purpose**: Track resource quotas and usage per user
- **Key Fields**: user_id (FK), max_tokens_per_day, used_tokens_today, reset_date
- **Relationships**: N:1 with users
- **Features**: Automatic daily reset tracking

#### agent_assignments
- **Purpose**: Map users to agent configurations with allocation strategies
- **Key Fields**: user_id (FK), agent_id_reference, allocation_strategy (shared/dedicated/pool)
- **Relationships**: N:1 with users
- **Features**: Priority-based assignment, concurrent request limits

#### usage_metrics
- **Purpose**: Track token usage and costs for billing/analytics
- **Key Fields**: user_id (FK), tokens_used, cost, timestamp
- **Relationships**: N:1 with users
- **Features**: Optimized for time-series queries

## Running Migrations

### Local Development
```bash
cd management-service-db
liquibase update
```

### Docker
Migrations run automatically via docker-compose on service startup.

### Rollback
```bash
liquibase rollback-count 1  # Rollback last changeset
liquibase rollback-to-date 2025-01-01  # Rollback to specific date
```

## Database Naming Conventions

- Tables: snake_case, plural (users, quotas)
- Columns: snake_case (user_id, created_at)
- Foreign Keys: fk_<table>_<referenced_table>
- Indexes: idx_<table>_<columns>
- Constraints: chk_<table>_<column>

## Indexes

- **Performance**: Indexes on all foreign keys and frequently queried columns
- **Analytics**: Composite index on (user_id, timestamp) for usage queries
- **Lookups**: Unique indexes on email, (user_id, agent_id_reference)

## Triggers

- **update_updated_at_column()**: Automatically updates updated_at on row modification
- Applied to: users, quotas, agent_assignments
