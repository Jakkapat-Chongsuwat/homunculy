package handlers

import (
	"strings"

	"management-service/internal/infrastructure"
	"management-service/internal/usecases/user"

	"github.com/gofiber/fiber/v2"
)

// ChatHandler handles chat-related HTTP requests
type ChatHandler struct {
	executeChatUseCase *user.ExecuteChatUseCase
}

// NewChatHandler creates a new ChatHandler
func NewChatHandler(executeChatUseCase *user.ExecuteChatUseCase) *ChatHandler {
	return &ChatHandler{
		executeChatUseCase: executeChatUseCase,
	}
}

// ChatRequest represents the request to execute chat
type ChatRequest struct {
	UserID        string                `json:"user_id"`
	Message       string                `json:"message"`
	Configuration AgentConfigurationDTO `json:"configuration"`
}

// AgentConfigurationDTO represents agent configuration in HTTP request
type AgentConfigurationDTO struct {
	Provider     string              `json:"provider"`
	ModelName    string              `json:"model_name"`
	SystemPrompt string              `json:"system_prompt"`
	Temperature  float64             `json:"temperature"`
	MaxTokens    int                 `json:"max_tokens"`
	Personality  AgentPersonalityDTO `json:"personality"`
}

// AgentPersonalityDTO represents agent personality in HTTP request
type AgentPersonalityDTO struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Traits      map[string]interface{} `json:"traits"`
	Mood        string                 `json:"mood"`
}

// ChatResponse represents the response from chat execution
type ChatResponse struct {
	Message    string  `json:"message"`
	Confidence float64 `json:"confidence"`
	Reasoning  string  `json:"reasoning"`
}

// ExecuteChat handles POST /chat
func (h *ChatHandler) ExecuteChat(c *fiber.Ctx) error {
	var req ChatRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	// Validate required fields
	if req.UserID == "" || req.Message == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "user_id and message are required",
		})
	}

	// Convert DTO to infrastructure type
	agentConfig := infrastructure.AgentConfiguration{
		Provider:     req.Configuration.Provider,
		ModelName:    req.Configuration.ModelName,
		SystemPrompt: req.Configuration.SystemPrompt,
		Temperature:  req.Configuration.Temperature,
		MaxTokens:    req.Configuration.MaxTokens,
		Personality: infrastructure.AgentPersonality{
			Name:        req.Configuration.Personality.Name,
			Description: req.Configuration.Personality.Description,
			Traits:      req.Configuration.Personality.Traits,
			Mood:        req.Configuration.Personality.Mood,
		},
	}

	// Execute chat
	response, err := h.executeChatUseCase.Execute(c.Context(), req.UserID, req.Message, agentConfig)
	if err != nil {
		// Check if it's a quota error
		if strings.Contains(err.Error(), "quota exceeded") {
			return c.Status(fiber.StatusTooManyRequests).JSON(fiber.Map{
				"error": err.Error(),
			})
		}
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": err.Error(),
		})
	}

	// Build response
	resp := ChatResponse{
		Message:    response.Message,
		Confidence: response.Confidence,
		Reasoning:  response.Reasoning,
	}

	return c.Status(fiber.StatusOK).JSON(resp)
}
