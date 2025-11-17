package agent

import (
	"context"
	"management-service/internal/domain/entities"
	"management-service/internal/domain/services"
)

// CreateAgentUseCase handles the creation of new agents
type CreateAgentUseCase struct {
	agentService *services.AgentService
}

// NewCreateAgentUseCase creates a new CreateAgentUseCase
func NewCreateAgentUseCase(agentService *services.AgentService) *CreateAgentUseCase {
	return &CreateAgentUseCase{
		agentService: agentService,
	}
}

// Execute creates a new agent
func (uc *CreateAgentUseCase) Execute(ctx context.Context, req CreateAgentRequest) (*CreateAgentResponse, error) {
	agent, err := uc.agentService.CreateAgent(
		ctx,
		req.Name,
		req.Description,
		req.Model,
		req.Config,
	)
	if err != nil {
		return nil, err
	}

	return &CreateAgentResponse{
		Agent: agent,
	}, nil
}

// CreateAgentRequest represents the request to create an agent
type CreateAgentRequest struct {
	Name        string               `json:"name"`
	Description string               `json:"description"`
	Model       string               `json:"model"`
	Config      entities.AgentConfig `json:"config"`
}

// CreateAgentResponse represents the response from creating an agent
type CreateAgentResponse struct {
	Agent *entities.Agent `json:"agent"`
}

// GetAgentUseCase handles retrieving a single agent
type GetAgentUseCase struct {
	agentService *services.AgentService
}

// NewGetAgentUseCase creates a new GetAgentUseCase
func NewGetAgentUseCase(agentService *services.AgentService) *GetAgentUseCase {
	return &GetAgentUseCase{
		agentService: agentService,
	}
}

// Execute retrieves an agent by ID
func (uc *GetAgentUseCase) Execute(ctx context.Context, req GetAgentRequest) (*GetAgentResponse, error) {
	agent, err := uc.agentService.GetAgent(ctx, req.ID)
	if err != nil {
		return nil, err
	}

	return &GetAgentResponse{
		Agent: agent,
	}, nil
}

// GetAgentRequest represents the request to get an agent
type GetAgentRequest struct {
	ID string `json:"id"`
}

// GetAgentResponse represents the response from getting an agent
type GetAgentResponse struct {
	Agent *entities.Agent `json:"agent"`
}

// ListAgentsUseCase handles listing agents with pagination
type ListAgentsUseCase struct {
	agentService *services.AgentService
}

// NewListAgentsUseCase creates a new ListAgentsUseCase
func NewListAgentsUseCase(agentService *services.AgentService) *ListAgentsUseCase {
	return &ListAgentsUseCase{
		agentService: agentService,
	}
}

// Execute lists agents with pagination
func (uc *ListAgentsUseCase) Execute(ctx context.Context, req ListAgentsRequest) (*ListAgentsResponse, error) {
	agents, err := uc.agentService.ListAgents(ctx, req.Limit, req.Offset)
	if err != nil {
		return nil, err
	}

	return &ListAgentsResponse{
		Agents: agents,
		Limit:  req.Limit,
		Offset: req.Offset,
	}, nil
}

// ListAgentsRequest represents the request to list agents
type ListAgentsRequest struct {
	Limit  int `json:"limit"`
	Offset int `json:"offset"`
}

// ListAgentsResponse represents the response from listing agents
type ListAgentsResponse struct {
	Agents []*entities.Agent `json:"agents"`
	Limit  int               `json:"limit"`
	Offset int               `json:"offset"`
}

// UpdateAgentUseCase handles updating existing agents
type UpdateAgentUseCase struct {
	agentService *services.AgentService
}

// NewUpdateAgentUseCase creates a new UpdateAgentUseCase
func NewUpdateAgentUseCase(agentService *services.AgentService) *UpdateAgentUseCase {
	return &UpdateAgentUseCase{
		agentService: agentService,
	}
}

// Execute updates an agent
func (uc *UpdateAgentUseCase) Execute(ctx context.Context, req UpdateAgentRequest) (*UpdateAgentResponse, error) {
	agent, err := uc.agentService.UpdateAgent(ctx, req.ID, &req.Updates)
	if err != nil {
		return nil, err
	}

	return &UpdateAgentResponse{
		Agent: agent,
	}, nil
}

// UpdateAgentRequest represents the request to update an agent
type UpdateAgentRequest struct {
	ID      string                      `json:"id"`
	Updates services.AgentUpdateRequest `json:"updates"`
}

// UpdateAgentResponse represents the response from updating an agent
type UpdateAgentResponse struct {
	Agent *entities.Agent `json:"agent"`
}

// DeleteAgentUseCase handles deleting agents
type DeleteAgentUseCase struct {
	agentService *services.AgentService
}

// NewDeleteAgentUseCase creates a new DeleteAgentUseCase
func NewDeleteAgentUseCase(agentService *services.AgentService) *DeleteAgentUseCase {
	return &DeleteAgentUseCase{
		agentService: agentService,
	}
}

// Execute deletes an agent
func (uc *DeleteAgentUseCase) Execute(ctx context.Context, req DeleteAgentRequest) (*DeleteAgentResponse, error) {
	err := uc.agentService.DeleteAgent(ctx, req.ID)
	if err != nil {
		return nil, err
	}

	return &DeleteAgentResponse{
		Success: true,
		Message: "Agent deleted successfully",
	}, nil
}

// DeleteAgentRequest represents the request to delete an agent
type DeleteAgentRequest struct {
	ID string `json:"id"`
}

// DeleteAgentResponse represents the response from deleting an agent
type DeleteAgentResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

// ActivateAgentUseCase handles activating agents
type ActivateAgentUseCase struct {
	agentService *services.AgentService
}

// NewActivateAgentUseCase creates a new ActivateAgentUseCase
func NewActivateAgentUseCase(agentService *services.AgentService) *ActivateAgentUseCase {
	return &ActivateAgentUseCase{
		agentService: agentService,
	}
}

// Execute activates an agent
func (uc *ActivateAgentUseCase) Execute(ctx context.Context, req ActivateAgentRequest) (*ActivateAgentResponse, error) {
	err := uc.agentService.ActivateAgent(ctx, req.ID)
	if err != nil {
		return nil, err
	}

	return &ActivateAgentResponse{
		Success: true,
		Message: "Agent activated successfully",
	}, nil
}

// ActivateAgentRequest represents the request to activate an agent
type ActivateAgentRequest struct {
	ID string `json:"id"`
}

// ActivateAgentResponse represents the response from activating an agent
type ActivateAgentResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

// DeactivateAgentUseCase handles deactivating agents
type DeactivateAgentUseCase struct {
	agentService *services.AgentService
}

// NewDeactivateAgentUseCase creates a new DeactivateAgentUseCase
func NewDeactivateAgentUseCase(agentService *services.AgentService) *DeactivateAgentUseCase {
	return &DeactivateAgentUseCase{
		agentService: agentService,
	}
}

// Execute deactivates an agent
func (uc *DeactivateAgentUseCase) Execute(ctx context.Context, req DeactivateAgentRequest) (*DeactivateAgentResponse, error) {
	err := uc.agentService.DeactivateAgent(ctx, req.ID)
	if err != nil {
		return nil, err
	}

	return &DeactivateAgentResponse{
		Success: true,
		Message: "Agent deactivated successfully",
	}, nil
}

// DeactivateAgentRequest represents the request to deactivate an agent
type DeactivateAgentRequest struct {
	ID string `json:"id"`
}

// DeactivateAgentResponse represents the response from deactivating an agent
type DeactivateAgentResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}
