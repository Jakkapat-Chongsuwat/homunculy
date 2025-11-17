package routes

import (
	"time"

	"github.com/gofiber/fiber/v2"
	"go.uber.org/zap"
)

// loggingMiddleware logs HTTP requests
func loggingMiddleware(c *fiber.Ctx) error {
	start := time.Now()

	// Log the request
	zap.L().Info("Started request",
		zap.String("method", c.Method()),
		zap.String("path", c.Path()),
		zap.String("ip", c.IP()),
	)

	// Call the next handler
	err := c.Next()

	// Log the completion
	zap.L().Info("Completed request",
		zap.String("method", c.Method()),
		zap.String("path", c.Path()),
		zap.Duration("duration", time.Since(start)),
		zap.Int("status", c.Response().StatusCode()),
	)

	return err
}

// corsMiddleware adds CORS headers
func corsMiddleware(c *fiber.Ctx) error {
	// Set CORS headers
	c.Set("Access-Control-Allow-Origin", "*")
	c.Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
	c.Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

	// Handle preflight requests
	if c.Method() == "OPTIONS" {
		return c.SendStatus(fiber.StatusOK)
	}

	// Call the next handler
	return c.Next()
}

// contentTypeMiddleware sets the default content type
func contentTypeMiddleware(c *fiber.Ctx) error {
	// Set default content type
	c.Set("Content-Type", "application/json")

	// Call the next handler
	return c.Next()
}
