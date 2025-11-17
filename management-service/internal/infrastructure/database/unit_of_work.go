package database

import (
	"context"
	"fmt"

	"management-service/internal/infrastructure/database/sqlc"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// UnitOfWork represents a database transaction
type UnitOfWork interface {
	// Queries returns the sqlc Querier interface for executing queries
	Queries() sqlc.Querier

	// Commit commits the transaction
	Commit(ctx context.Context) error

	// Rollback rolls back the transaction
	Rollback(ctx context.Context) error
}

// PostgresUnitOfWork implements UnitOfWork with PostgreSQL transaction
type PostgresUnitOfWork struct {
	tx      pgx.Tx
	queries *sqlc.Queries
}

// NewUnitOfWork creates a new Unit of Work with a transaction
func NewUnitOfWork(ctx context.Context, pool *pgxpool.Pool) (UnitOfWork, error) {
	tx, err := pool.Begin(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}

	return &PostgresUnitOfWork{
		tx:      tx,
		queries: sqlc.New(tx),
	}, nil
}

// Queries returns the sqlc Querier for the transaction
func (uow *PostgresUnitOfWork) Queries() sqlc.Querier {
	return uow.queries
}

// Commit commits the transaction
func (uow *PostgresUnitOfWork) Commit(ctx context.Context) error {
	if err := uow.tx.Commit(ctx); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}
	return nil
}

// Rollback rolls back the transaction
func (uow *PostgresUnitOfWork) Rollback(ctx context.Context) error {
	if err := uow.tx.Rollback(ctx); err != nil {
		// Ignore "transaction already committed" errors
		if err != pgx.ErrTxClosed {
			return fmt.Errorf("failed to rollback transaction: %w", err)
		}
	}
	return nil
}
