package handlers

import (
	"management-service/internal/usecases/agent"
	"strconv"
	"strings"

	"github.com/gofiber/fiber/v2"
)

// AgentHandler handles HTTP requests for agent operations
type AgentHandler struct {
	createAgentUseCase     *agent.CreateAgentUseCase
	getAgentUseCase        *agent.GetAgentUseCase
	listAgentsUseCase      *agent.ListAgentsUseCase
	updateAgentUseCase     *agent.UpdateAgentUseCase
	deleteAgentUseCase     *agent.DeleteAgentUseCase
	activateAgentUseCase   *agent.ActivateAgentUseCase
	deactivateAgentUseCase *agent.DeactivateAgentUseCase
}

// NewAgentHandler creates a new agent handler
func NewAgentHandler(
	createUC *agent.CreateAgentUseCase,
	getUC *agent.GetAgentUseCase,
	listUC *agent.ListAgentsUseCase,
	updateUC *agent.UpdateAgentUseCase,
	deleteUC *agent.DeleteAgentUseCase,
	activateUC *agent.ActivateAgentUseCase,
	deactivateUC *agent.DeactivateAgentUseCase,
) *AgentHandler {
	return &AgentHandler{
		createAgentUseCase:     createUC,
		getAgentUseCase:        getUC,
		listAgentsUseCase:      listUC,
		updateAgentUseCase:     updateUC,
		deleteAgentUseCase:     deleteUC,
		activateAgentUseCase:   activateUC,
		deactivateAgentUseCase: deactivateUC,
	}
}

// CreateAgent handles POST /agents
func (h *AgentHandler) CreateAgent(c *fiber.Ctx) error {
	var req agent.CreateAgentRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid request body"})
	}

	response, err := h.createAgentUseCase.Execute(c.Context(), req)
	if err != nil {
		return h.handleError(c, err)
	}

	return c.Status(fiber.StatusCreated).JSON(response)
}

// GetAgent handles GET /agents/{id}
func (h *AgentHandler) GetAgent(c *fiber.Ctx) error {
	id := c.Params("id")
	if id == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Agent ID is required"})
	}

	req := agent.GetAgentRequest{ID: id}
	response, err := h.getAgentUseCase.Execute(c.Context(), req)
	if err != nil {
		return h.handleError(c, err)
	}

	return c.JSON(response)
}

// ListAgents handles GET /agents
func (h *AgentHandler) ListAgents(c *fiber.Ctx) error {
	// Parse query parameters
	limit := h.parseIntParam(c, "limit", 10)
	offset := h.parseIntParam(c, "offset", 0)

	req := agent.ListAgentsRequest{
		Limit:  limit,
		Offset: offset,
	}

	response, err := h.listAgentsUseCase.Execute(c.Context(), req)
	if err != nil {
		return h.handleError(c, err)
	}

	return c.JSON(response)
}

// UpdateAgent handles PUT /agents/{id}
func (h *AgentHandler) UpdateAgent(c *fiber.Ctx) error {
	id := c.Params("id")
	if id == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Agent ID is required"})
	}

	var updates agent.UpdateAgentRequest
	if err := c.BodyParser(&updates); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid request body"})
	}
	updates.ID = id

	response, err := h.updateAgentUseCase.Execute(c.Context(), updates)
	if err != nil {
		return h.handleError(c, err)
	}

	return c.JSON(response)
}

// DeleteAgent handles DELETE /agents/{id}
func (h *AgentHandler) DeleteAgent(c *fiber.Ctx) error {
	id := c.Params("id")
	if id == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Agent ID is required"})
	}

	req := agent.DeleteAgentRequest{ID: id}
	response, err := h.deleteAgentUseCase.Execute(c.Context(), req)
	if err != nil {
		return h.handleError(c, err)
	}

	return c.JSON(response)
}

// ActivateAgent handles POST /agents/{id}/activate
func (h *AgentHandler) ActivateAgent(c *fiber.Ctx) error {
	id := c.Params("id")
	if id == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Agent ID is required"})
	}

	req := agent.ActivateAgentRequest{ID: id}
	response, err := h.activateAgentUseCase.Execute(c.Context(), req)
	if err != nil {
		return h.handleError(c, err)
	}

	return c.JSON(response)
}

// DeactivateAgent handles POST /agents/{id}/deactivate
func (h *AgentHandler) DeactivateAgent(c *fiber.Ctx) error {
	id := c.Params("id")
	if id == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Agent ID is required"})
	}

	req := agent.DeactivateAgentRequest{ID: id}
	response, err := h.deactivateAgentUseCase.Execute(c.Context(), req)
	if err != nil {
		return h.handleError(c, err)
	}

	return c.JSON(response)
}

// HealthCheck handles GET /health
func (h *AgentHandler) HealthCheck(c *fiber.Ctx) error {
	response := fiber.Map{
		"status":  "healthy",
		"service": "management-service",
	}
	return c.JSON(response)
}

// Helper methods

// handleError handles domain errors and converts them to HTTP responses
func (h *AgentHandler) handleError(c *fiber.Ctx, err error) error {
	switch {
	case strings.Contains(err.Error(), "not found"):
		return c.Status(fiber.StatusNotFound).JSON(fiber.Map{"error": err.Error()})
	case strings.Contains(err.Error(), "already exists"):
		return c.Status(fiber.StatusConflict).JSON(fiber.Map{"error": err.Error()})
	case strings.Contains(err.Error(), "validation failed"):
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
	case strings.Contains(err.Error(), "invalid"):
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
	default:
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": "Internal server error"})
	}
}

// parseIntParam parses an integer query parameter with a default value
func (h *AgentHandler) parseIntParam(c *fiber.Ctx, key string, defaultValue int) int {
	param := c.Query(key)
	if param == "" {
		return defaultValue
	}

	value, err := strconv.Atoi(param)
	if err != nil {
		return defaultValue
	}

	return value
}
