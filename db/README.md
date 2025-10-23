# Database Migrations

This directory contains Liquibase database migration files for the Homunculy AI Agent system.

## Directory Structure

```
db/
├── changelog/
│   ├── db.changelog-master.xml    # Master changelog file - entry point for all migrations
│   └── changesets/                # Individual migration files
│       ├── 001-initial-schema.sql # Initial database schema
│       └── ...                    # Future migration files
└── README.md                      # This file
```

## Migration File Naming Convention

Migration files follow the pattern: `NNN-description.sql`

- `NNN`: Three-digit sequential number (001, 002, 003, etc.)
- `description`: Brief description of the change in kebab-case

## Adding New Migrations

1. Create a new SQL file in `changesets/` directory
2. Use the Liquibase SQL format with proper changeset headers:

```sql
--liquibase formatted sql

--changeset yourname:NNN-description
--comment: Description of the database change

-- Your SQL statements here
```

3. Update `db.changelog-master.xml` to include the new file
4. Test the migration locally before committing

## Running Migrations

Use the provided scripts:

- Windows PowerShell: `.\scripts\run-migrations.ps1`
- Linux/Mac: `./scripts/run-migrations.sh`

## Best Practices

- Each changeset should be atomic and reversible when possible
- Use meaningful changeset IDs and descriptions
- Test migrations on a copy of production data before applying
- Never modify existing changesets - create new ones for changes
- Keep migrations idempotent (safe to run multiple times)