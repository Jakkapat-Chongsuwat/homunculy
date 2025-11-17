package postgres

import (
	"context"
	"fmt"
	"time"

	"management-service/internal/infrastructure/config"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Connection wraps pgxpool for database operations
type Connection struct {
	pool *pgxpool.Pool
}

// NewConnection creates a new PostgreSQL connection pool
func NewConnection(cfg *config.DatabaseConfig) (*Connection, error) {
	// Build connection string
	connString := fmt.Sprintf(
		"postgres://%s:%s@%s:%d/%s?sslmode=%s",
		cfg.User,
		cfg.Password,
		cfg.Host,
		cfg.Port,
		cfg.Database,
		cfg.SSLMode,
	)

	// Configure connection pool
	poolConfig, err := pgxpool.ParseConfig(connString)
	if err != nil {
		return nil, fmt.Errorf("failed to parse connection config: %w", err)
	}

	// Set pool settings
	poolConfig.MaxConns = int32(cfg.MaxConnections)
	poolConfig.MinConns = 2
	poolConfig.MaxConnLifetime = time.Hour
	poolConfig.MaxConnIdleTime = 30 * time.Minute
	poolConfig.HealthCheckPeriod = time.Minute

	// Create connection pool with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	pool, err := pgxpool.NewWithConfig(ctx, poolConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	// Verify connection
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &Connection{pool: pool}, nil
}

// GetPool returns the underlying connection pool
func (c *Connection) GetPool() *pgxpool.Pool {
	return c.pool
}

// Close closes the connection pool
func (c *Connection) Close() {
	if c.pool != nil {
		c.pool.Close()
	}
}

// Ping verifies the connection is alive
func (c *Connection) Ping(ctx context.Context) error {
	return c.pool.Ping(ctx)
}
