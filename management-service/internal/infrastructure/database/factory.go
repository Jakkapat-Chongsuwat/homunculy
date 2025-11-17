package database

import (
	"fmt"
	"management-service/internal/domain/repositories"
	"management-service/internal/infrastructure/config"
	"management-service/internal/infrastructure/database/postgres"

	"github.com/jackc/pgx/v5/pgxpool"
	"go.uber.org/zap"
)

// DatabaseType represents the type of database backend
type DatabaseType string

const (
	// PostgreSQL database type
	PostgreSQL DatabaseType = "postgres"
	// MySQL database type (future implementation)
	MySQL DatabaseType = "mysql"
)

// DatabaseFactory creates database connections and repositories
type DatabaseFactory struct {
	dbType      DatabaseType
	config      *config.DatabaseConfig
	logger      *zap.Logger
	pgConn      *postgres.Connection
	pgUserRepo  *postgres.UserRepository
	pgQuotaRepo *postgres.QuotaRepository
}

// NewDatabaseFactory creates a new database factory
func NewDatabaseFactory(dbType DatabaseType, cfg *config.DatabaseConfig, logger *zap.Logger) *DatabaseFactory {
	return &DatabaseFactory{
		dbType: dbType,
		config: cfg,
		logger: logger,
	}
}

// Initialize initializes the database connection and repositories
func (f *DatabaseFactory) Initialize() error {
	switch f.dbType {
	case PostgreSQL:
		return f.initializePostgreSQL()
	case MySQL:
		return fmt.Errorf("MySQL not yet implemented")
	default:
		return fmt.Errorf("unsupported database type: %s", f.dbType)
	}
}

// initializePostgreSQL sets up PostgreSQL connection and repositories
func (f *DatabaseFactory) initializePostgreSQL() error {
	conn, err := postgres.NewConnection(f.config)
	if err != nil {
		return fmt.Errorf("failed to connect to PostgreSQL: %w", err)
	}

	f.pgConn = conn
	f.pgUserRepo = postgres.NewUserRepository(conn.GetPool())
	f.pgQuotaRepo = postgres.NewQuotaRepository(conn.GetPool())

	f.logger.Info("PostgreSQL connection established",
		zap.String("host", f.config.Host),
		zap.Int("port", f.config.Port),
		zap.String("database", f.config.Database),
	)

	return nil
}

// GetUserRepository returns the user repository
func (f *DatabaseFactory) GetUserRepository() (repositories.UserRepository, error) {
	if f.pgUserRepo == nil {
		return nil, fmt.Errorf("database not initialized, call Initialize() first")
	}
	return f.pgUserRepo, nil
}

// GetQuotaRepository returns the quota repository
func (f *DatabaseFactory) GetQuotaRepository() (*postgres.QuotaRepository, error) {
	if f.pgQuotaRepo == nil {
		return nil, fmt.Errorf("database not initialized, call Initialize() first")
	}
	return f.pgQuotaRepo, nil
}

// GetPool returns the PostgreSQL connection pool
func (f *DatabaseFactory) GetPool() (*pgxpool.Pool, error) {
	if f.pgConn == nil {
		return nil, fmt.Errorf("database not initialized, call Initialize() first")
	}
	return f.pgConn.GetPool(), nil
}

// CreateAgentRepository creates an agent repository based on the configured database type
func (f *DatabaseFactory) CreateAgentRepository() (repositories.AgentRepository, error) {
	switch f.dbType {
	case PostgreSQL:
		return nil, fmt.Errorf("PostgreSQL agent repository not yet implemented")
	case MySQL:
		return nil, fmt.Errorf("MySQL repository not yet implemented")
	default:
		return nil, fmt.Errorf("unsupported database type: %s", f.dbType)
	}
}

// Close closes all database connections
func (f *DatabaseFactory) Close() error {
	if f.pgConn != nil {
		f.pgConn.Close()
		f.logger.Info("PostgreSQL connection closed")
	}
	return nil
}
