package routes

import (
	"management-service/internal/adapters/http/handlers"

	"github.com/gofiber/fiber/v2"
)

// SetupRoutes configures all HTTP routes for the application
func SetupRoutes(
	app *fiber.App,
	agentHandler *handlers.AgentHandler,
	userHandler *handlers.UserHandler,
	chatHandler *handlers.ChatHandler,
) {
	// API v1 routes
	api := app.Group("/api/v1")

	// Agent routes (agent configuration management)
	api.Post("/agents", agentHandler.CreateAgent)
	api.Get("/agents", agentHandler.ListAgents)
	api.Get("/agents/:id", agentHandler.GetAgent)
	api.Put("/agents/:id", agentHandler.UpdateAgent)
	api.Delete("/agents/:id", agentHandler.DeleteAgent)
	api.Post("/agents/:id/activate", agentHandler.ActivateAgent)
	api.Post("/agents/:id/deactivate", agentHandler.DeactivateAgent)

	// User routes (only register if handler is available)
	if userHandler != nil {
		api.Post("/users", userHandler.CreateUser)
	}

	// Chat routes (proxies to Homunculy execution engine - only register if handler is available)
	if chatHandler != nil {
		api.Post("/chat", chatHandler.ExecuteChat)
	}

	// LiveKit routes removed

	// Health check
	if agentHandler != nil {
		api.Get("/health", agentHandler.HealthCheck)
	}

	// Add middleware
	app.Use(loggingMiddleware)
	app.Use(corsMiddleware)
	app.Use(contentTypeMiddleware)
}
