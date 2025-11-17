package repositories

import (
	"context"
	"management-service/internal/domain/entities"
)

// AgentRepository defines the interface for agent data operations
type AgentRepository interface {
	// Create saves a new agent to the repository
	Create(ctx context.Context, agent *entities.Agent) error

	// GetByID retrieves an agent by its ID
	GetByID(ctx context.Context, id string) (*entities.Agent, error)

	// GetByName retrieves an agent by its name
	GetByName(ctx context.Context, name string) (*entities.Agent, error)

	// List retrieves all agents with optional filtering
	List(ctx context.Context, limit, offset int) ([]*entities.Agent, error)

	// Update modifies an existing agent
	Update(ctx context.Context, agent *entities.Agent) error

	// Delete removes an agent by ID
	Delete(ctx context.Context, id string) error

	// Exists checks if an agent with the given ID exists
	Exists(ctx context.Context, id string) (bool, error)

	// Count returns the total number of agents
	Count(ctx context.Context) (int64, error)
}
