package services

import (
	"context"
	"errors"
	"fmt"
	"management-service/internal/domain/entities"
	"management-service/internal/domain/repositories"
)

// AgentService handles agent-related business logic
type AgentService struct {
	repo repositories.AgentRepository
}

// NewAgentService creates a new agent service
func NewAgentService(repo repositories.AgentRepository) *AgentService {
	return &AgentService{
		repo: repo,
	}
}

// CreateAgent creates a new agent with validation
func (s *AgentService) CreateAgent(ctx context.Context, name, description, model string, config entities.AgentConfig) (*entities.Agent, error) {
	// Validate input
	if err := s.validateAgentData(name, description, model, config); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Check if agent with same name already exists
	existing, err := s.repo.GetByName(ctx, name)
	if err != nil && !errors.Is(err, ErrNotFound) {
		return nil, fmt.Errorf("failed to check existing agent: %w", err)
	}
	if existing != nil {
		return nil, fmt.Errorf("agent with name '%s' already exists", name)
	}

	// Create new agent
	agent := entities.NewAgent(name, description, model, config)

	// Save to repository
	if err := s.repo.Create(ctx, agent); err != nil {
		return nil, fmt.Errorf("failed to create agent: %w", err)
	}

	return agent, nil
}

// GetAgent retrieves an agent by ID
func (s *AgentService) GetAgent(ctx context.Context, id string) (*entities.Agent, error) {
	if id == "" {
		return nil, errors.New("agent ID cannot be empty")
	}

	agent, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("failed to get agent: %w", err)
	}

	return agent, nil
}

// UpdateAgent updates an existing agent
func (s *AgentService) UpdateAgent(ctx context.Context, id string, updates *AgentUpdateRequest) (*entities.Agent, error) {
	if id == "" {
		return nil, errors.New("agent ID cannot be empty")
	}

	// Get existing agent
	agent, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("failed to get agent for update: %w", err)
	}

	// Apply updates
	if updates.Name != nil {
		agent.Name = *updates.Name
	}
	if updates.Description != nil {
		agent.Description = *updates.Description
	}
	if updates.Model != nil {
		agent.Model = *updates.Model
	}
	if updates.Config != nil {
		agent.UpdateConfig(*updates.Config)
	}

	// Validate updated agent
	if err := s.validateAgentData(agent.Name, agent.Description, agent.Model, agent.Config); err != nil {
		return nil, fmt.Errorf("validation failed for updated agent: %w", err)
	}

	// Save updates
	if err := s.repo.Update(ctx, agent); err != nil {
		return nil, fmt.Errorf("failed to update agent: %w", err)
	}

	return agent, nil
}

// DeleteAgent removes an agent
func (s *AgentService) DeleteAgent(ctx context.Context, id string) error {
	if id == "" {
		return errors.New("agent ID cannot be empty")
	}

	// Check if agent exists
	exists, err := s.repo.Exists(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to check agent existence: %w", err)
	}
	if !exists {
		return ErrNotFound
	}

	// Delete agent
	if err := s.repo.Delete(ctx, id); err != nil {
		return fmt.Errorf("failed to delete agent: %w", err)
	}

	return nil
}

// ListAgents retrieves agents with pagination
func (s *AgentService) ListAgents(ctx context.Context, limit, offset int) ([]*entities.Agent, error) {
	if limit < 0 || offset < 0 {
		return nil, errors.New("limit and offset must be non-negative")
	}

	agents, err := s.repo.List(ctx, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to list agents: %w", err)
	}

	return agents, nil
}

// ActivateAgent activates an agent
func (s *AgentService) ActivateAgent(ctx context.Context, id string) error {
	return s.updateAgentStatus(ctx, id, entities.AgentStatusActive)
}

// DeactivateAgent deactivates an agent
func (s *AgentService) DeactivateAgent(ctx context.Context, id string) error {
	return s.updateAgentStatus(ctx, id, entities.AgentStatusInactive)
}

// updateAgentStatus is a helper method to update agent status
func (s *AgentService) updateAgentStatus(ctx context.Context, id string, status entities.AgentStatus) error {
	agent, err := s.GetAgent(ctx, id)
	if err != nil {
		return err
	}

	switch status {
	case entities.AgentStatusActive:
		agent.Activate()
	case entities.AgentStatusInactive:
		agent.Deactivate()
	default:
		return fmt.Errorf("invalid status: %s", status)
	}

	if err := s.repo.Update(ctx, agent); err != nil {
		return fmt.Errorf("failed to update agent status: %w", err)
	}

	return nil
}

// validateAgentData validates agent input data
func (s *AgentService) validateAgentData(name, description, model string, config entities.AgentConfig) error {
	if name == "" {
		return errors.New("agent name cannot be empty")
	}
	if len(name) > 100 {
		return errors.New("agent name cannot exceed 100 characters")
	}
	if description == "" {
		return errors.New("agent description cannot be empty")
	}
	if len(description) > 500 {
		return errors.New("agent description cannot exceed 500 characters")
	}
	if model == "" {
		return errors.New("agent model cannot be empty")
	}
	if config.Temperature < 0 || config.Temperature > 2 {
		return errors.New("temperature must be between 0 and 2")
	}
	if config.MaxTokens < 1 || config.MaxTokens > 4096 {
		return errors.New("max tokens must be between 1 and 4096")
	}
	return nil
}

// AgentUpdateRequest represents fields that can be updated for an agent
type AgentUpdateRequest struct {
	Name        *string               `json:"name,omitempty"`
	Description *string               `json:"description,omitempty"`
	Model       *string               `json:"model,omitempty"`
	Config      *entities.AgentConfig `json:"config,omitempty"`
}

// Common errors
var (
	ErrNotFound = errors.New("agent not found")
)
