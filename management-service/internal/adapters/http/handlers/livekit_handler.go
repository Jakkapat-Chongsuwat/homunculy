package handlers

import (
	"management-service/internal/usecases/livekit"

	"github.com/gofiber/fiber/v2"
)

// LiveKitHandler handles LiveKit token requests.
type LiveKitHandler struct {
	createToken *livekit.CreateTokenUseCase
}

// NewLiveKitHandler creates a new handler.
func NewLiveKitHandler(createToken *livekit.CreateTokenUseCase) *LiveKitHandler {
	return &LiveKitHandler{createToken: createToken}
}

// CreateToken handles POST /livekit/token.
func (h *LiveKitHandler) CreateToken(c *fiber.Ctx) error {
	req, err := parseTokenRequest(c)
	if err != nil {
		return err
	}
	res, err := h.createToken.Execute(c.Context(), *req)
	return respondToken(c, res, err)
}

func parseTokenRequest(c *fiber.Ctx) (*livekit.CreateTokenRequest, error) {
	var req livekit.CreateTokenRequest
	if err := c.BodyParser(&req); err != nil {
		return nil, c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid request body"})
	}
	return &req, nil
}

func respondToken(c *fiber.Ctx, res *livekit.CreateTokenResponse, err error) error {
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": err.Error()})
	}
	return c.JSON(res)
}
