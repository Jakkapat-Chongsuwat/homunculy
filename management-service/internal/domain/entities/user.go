// Package entities contains domain entities for the management service
package entities

import "time"

// SubscriptionTier represents user subscription levels
type SubscriptionTier string

const (
	SubscriptionTierFree       SubscriptionTier = "free"
	SubscriptionTierPremium    SubscriptionTier = "premium"
	SubscriptionTierEnterprise SubscriptionTier = "enterprise"
	// Legacy constants for backward compatibility
	TierFree       SubscriptionTier = "free"
	TierPremium    SubscriptionTier = "premium"
	TierEnterprise SubscriptionTier = "enterprise"
)

// User represents a system user
type User struct {
	ID               string           `json:"id"`
	Email            string           `json:"email"`
	Name             string           `json:"name"`
	SubscriptionTier SubscriptionTier `json:"subscription_tier"`
	IsActive         bool             `json:"is_active"`
	CreatedAt        time.Time        `json:"created_at"`
	UpdatedAt        time.Time        `json:"updated_at"`
}

// AllocationStrategy defines how agents are allocated to users
type AllocationStrategy string

const (
	StrategyShared    AllocationStrategy = "shared"    // User shares agent with others
	StrategyDedicated AllocationStrategy = "dedicated" // User has exclusive agent
	StrategyPool      AllocationStrategy = "pool"      // User accesses pool of agents
)

// AgentAssignment represents the assignment of an agent to a user
type AgentAssignment struct {
	ID                    string             `json:"id"`
	UserID                string             `json:"user_id"`
	AgentIDReference      string             `json:"agent_id_reference"`
	AllocationStrategy    AllocationStrategy `json:"allocation_strategy"`
	Priority              int32              `json:"priority"`
	MaxConcurrentRequests int32              `json:"max_concurrent_requests"`
	CreatedAt             time.Time          `json:"created_at"`
	UpdatedAt             time.Time          `json:"updated_at"`
}

// UsageMetric tracks resource usage for billing and analytics
type UsageMetric struct {
	ID               string    `json:"id"`
	UserID           string    `json:"user_id"`
	AgentIDReference string    `json:"agent_id_reference"`
	TokensUsed       int64     `json:"tokens_used"`
	RequestsCount    int64     `json:"requests_count"`
	Cost             float64   `json:"cost"`
	Timestamp        time.Time `json:"timestamp"`
}

// Quota represents user's resource quotas
type Quota struct {
	ID                   string           `json:"id"`
	UserID               string           `json:"user_id"`
	Tier                 SubscriptionTier `json:"tier"`
	MaxAgents            int32            `json:"max_agents"`
	MaxTokensPerDay      int64            `json:"max_tokens_per_day"`
	MaxRequestsPerDay    int32            `json:"max_requests_per_day"`
	MaxRequestsPerMinute int32            `json:"max_requests_per_minute"`
	UsedTokensToday      int32            `json:"used_tokens_today"`
	UsedRequestsToday    int32            `json:"used_requests_today"`
	ResetDate            time.Time        `json:"reset_date"`
	CreatedAt            time.Time        `json:"created_at"`
	UpdatedAt            time.Time        `json:"updated_at"`
}
