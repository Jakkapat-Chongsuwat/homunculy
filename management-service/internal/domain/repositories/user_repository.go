// Package repositories defines repository interfaces for domain entities
package repositories

import (
	"context"
	"management-service/internal/domain/entities"
)

// UserRepository defines the interface for user persistence operations
type UserRepository interface {
	Create(ctx context.Context, user *entities.User) error
	GetByID(ctx context.Context, userID string) (*entities.User, error)
	GetByEmail(ctx context.Context, email string) (*entities.User, error)
	Update(ctx context.Context, user *entities.User) error
	Delete(ctx context.Context, userID string) error
	ListAll(ctx context.Context, limit, offset int) ([]*entities.User, error)
}

// AssignmentRepository defines the interface for agent assignment operations
type AssignmentRepository interface {
	Create(ctx context.Context, assignment *entities.AgentAssignment) error
	GetByID(ctx context.Context, assignmentID string) (*entities.AgentAssignment, error)
	GetByUserID(ctx context.Context, userID string) ([]*entities.AgentAssignment, error)
	GetByAgentID(ctx context.Context, agentID string) ([]*entities.AgentAssignment, error)
	Delete(ctx context.Context, assignmentID string) error
	DeleteByUserAndAgent(ctx context.Context, userID, agentID string) error
}

// UsageRepository defines the interface for usage metrics operations
type UsageRepository interface {
	Create(ctx context.Context, metric *entities.UsageMetric) error
	GetByUserID(ctx context.Context, userID string, limit int) ([]*entities.UsageMetric, error)
	GetByUserIDAndDateRange(ctx context.Context, userID string, start, end interface{}) ([]*entities.UsageMetric, error)
	GetTotalUsageByUser(ctx context.Context, userID string) (*entities.UsageMetric, error)
}

// QuotaRepository defines the interface for quota operations
type QuotaRepository interface {
	Create(ctx context.Context, quota *entities.Quota) error
	GetByUserID(ctx context.Context, userID string) (*entities.Quota, error)
	Update(ctx context.Context, quota *entities.Quota) error
	Delete(ctx context.Context, userID string) error
}
