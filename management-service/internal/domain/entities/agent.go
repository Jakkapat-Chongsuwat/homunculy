package entities

import (
	"time"
)

// AgentStatus represents the current status of an AI agent
type AgentStatus string

const (
	AgentStatusActive   AgentStatus = "active"
	AgentStatusInactive AgentStatus = "inactive"
	AgentStatusError    AgentStatus = "error"
)

// Agent represents an AI agent entity (Pure Domain Model - No Infrastructure Concerns)
type Agent struct {
	ID          string
	Name        string
	Description string
	Model       string
	Status      AgentStatus
	Config      AgentConfig
	CreatedAt   time.Time
	UpdatedAt   time.Time
}

// AgentConfig holds configuration settings for an agent
type AgentConfig struct {
	Temperature    float64
	MaxTokens      int
	SystemPrompt   string
	ResponseFormat string
	ToolsEnabled   bool
	MemoryEnabled  bool
}

// NewAgent creates a new agent with default values
func NewAgent(name, description, model string, config AgentConfig) *Agent {
	now := time.Now()
	return &Agent{
		Name:        name,
		Description: description,
		Model:       model,
		Status:      AgentStatusInactive,
		Config:      config,
		CreatedAt:   now,
		UpdatedAt:   now,
	}
}

// IsActive returns true if the agent is active
func (a *Agent) IsActive() bool {
	return a.Status == AgentStatusActive
}

// Activate sets the agent status to active
func (a *Agent) Activate() {
	a.Status = AgentStatusActive
	a.UpdatedAt = time.Now()
}

// Deactivate sets the agent status to inactive
func (a *Agent) Deactivate() {
	a.Status = AgentStatusInactive
	a.UpdatedAt = time.Now()
}

// UpdateConfig updates the agent configuration
func (a *Agent) UpdateConfig(config AgentConfig) {
	a.Config = config
	a.UpdatedAt = time.Now()
}

// Validate performs business validation on the agent
func (a *Agent) Validate() error {
	if a.Name == "" {
		return ErrInvalidAgentName
	}
	if a.Model == "" {
		return ErrInvalidAgentModel
	}
	if a.Config.MaxTokens <= 0 {
		return ErrInvalidMaxTokens
	}
	if a.Config.Temperature < 0 || a.Config.Temperature > 2 {
		return ErrInvalidTemperature
	}
	return nil
}

// Domain errors
var (
	ErrInvalidAgentName   = DomainError{Message: "agent name cannot be empty"}
	ErrInvalidAgentModel  = DomainError{Message: "agent model cannot be empty"}
	ErrInvalidMaxTokens   = DomainError{Message: "max tokens must be greater than 0"}
	ErrInvalidTemperature = DomainError{Message: "temperature must be between 0 and 2"}
	ErrAgentNotFound      = DomainError{Message: "agent not found"}
	ErrAgentAlreadyExists = DomainError{Message: "agent already exists"}
)

// DomainError represents a domain-level error
type DomainError struct {
	Message string
}

func (e DomainError) Error() string {
	return e.Message
}
