package handlers

import (
	"management-service/internal/domain/entities"
	"management-service/internal/usecases/user"

	"github.com/gofiber/fiber/v2"
)

// UserHandler handles user-related HTTP requests
type UserHandler struct {
	createUserUseCase *user.CreateUserUseCase
}

// NewUserHandler creates a new UserHandler
func NewUserHandler(createUserUseCase *user.CreateUserUseCase) *UserHandler {
	return &UserHandler{
		createUserUseCase: createUserUseCase,
	}
}

// CreateUserRequest represents the request to create a user
type CreateUserRequest struct {
	Email            string `json:"email"`
	Name             string `json:"name"`
	SubscriptionTier string `json:"subscription_tier"`
}

// CreateUserResponse represents the response from creating a user
type CreateUserResponse struct {
	ID               string `json:"id"`
	Email            string `json:"email"`
	Name             string `json:"name"`
	SubscriptionTier string `json:"subscription_tier"`
	IsActive         bool   `json:"is_active"`
}

// CreateUser handles POST /users
func (h *UserHandler) CreateUser(c *fiber.Ctx) error {
	var req CreateUserRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	// Parse subscription tier
	tier := entities.SubscriptionTier(req.SubscriptionTier)
	if tier != entities.SubscriptionTierFree &&
		tier != entities.SubscriptionTierPremium &&
		tier != entities.SubscriptionTierEnterprise {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid subscription tier",
		})
	}

	// Create user
	user, err := h.createUserUseCase.Execute(c.Context(), req.Email, req.Name, tier)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": err.Error(),
		})
	}

	// Build response
	resp := CreateUserResponse{
		ID:               user.ID,
		Email:            user.Email,
		Name:             user.Name,
		SubscriptionTier: string(user.SubscriptionTier),
		IsActive:         user.IsActive,
	}

	return c.Status(fiber.StatusCreated).JSON(resp)
}
