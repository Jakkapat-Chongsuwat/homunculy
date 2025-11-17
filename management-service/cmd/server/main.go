package main

import (
	"context"
	"fmt"
	"log"
	"management-service/internal/adapters/http/handlers"
	"management-service/internal/adapters/http/routes"
	"management-service/internal/domain/services"
	"management-service/internal/infrastructure/config"
	"management-service/internal/infrastructure/database"
	"management-service/internal/usecases/agent"
	"os"
	"os/signal"
	"syscall"

	"github.com/gofiber/fiber/v2"
	"go.uber.org/zap"
)

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func main() {
	// Initialize logger
	logger, err := zap.NewProduction()
	if err != nil {
		log.Fatalf("Failed to initialize logger: %v", err)
	}
	defer logger.Sync()

	// Load configuration
	cfg := config.Load()
	logger.Info("Configuration loaded", zap.String("host", cfg.Server.Host), zap.Int("port", cfg.Server.Port))

	// Initialize database factory
	dbFactory := database.NewDatabaseFactory(database.PostgreSQL, &cfg.Database, logger)
	defer dbFactory.Close()

	// Initialize database connection
	if err := dbFactory.Initialize(); err != nil {
		logger.Fatal("Failed to initialize database", zap.Error(err))
	}

	// Get connection pool for Unit of Work
	pool, err := dbFactory.GetPool()
	if err != nil {
		logger.Fatal("Failed to get database pool", zap.Error(err))
	}

	// Create Unit of Work factory
	uowFactory := func(ctx context.Context) (database.UnitOfWork, error) {
		return database.NewUnitOfWork(ctx, pool)
	}

	// Get repositories
	userRepo, err := dbFactory.GetUserRepository()
	if err != nil {
		logger.Fatal("Failed to get user repository", zap.Error(err))
	}

	quotaRepo, err := dbFactory.GetQuotaRepository()
	if err != nil {
		logger.Fatal("Failed to get quota repository", zap.Error(err))
	}

	// Create repositories using factory pattern (agents not yet implemented)
	// Note: Agent repository is not yet implemented for PostgreSQL
	logger.Info("Agent repository not yet implemented - skipping agent handler initialization")
	var agentHandler *handlers.AgentHandler = nil
	if false { // Disabled until PostgreSQL agent repository is implemented
		agentRepo, err := dbFactory.CreateAgentRepository()
		if err != nil {
			logger.Warn("Agent repository not yet implemented", zap.Error(err))
		}
		agentService := services.NewAgentService(agentRepo)
		createAgentUC := agent.NewCreateAgentUseCase(agentService)
		getAgentUC := agent.NewGetAgentUseCase(agentService)
		listAgentsUC := agent.NewListAgentsUseCase(agentService)
		updateAgentUC := agent.NewUpdateAgentUseCase(agentService)
		deleteAgentUC := agent.NewDeleteAgentUseCase(agentService)
		activateAgentUC := agent.NewActivateAgentUseCase(agentService)
		deactivateAgentUC := agent.NewDeactivateAgentUseCase(agentService)

		agentHandler = handlers.NewAgentHandler(
			createAgentUC,
			getAgentUC,
			listAgentsUC,
			updateAgentUC,
			deleteAgentUC,
			activateAgentUC,
			deactivateAgentUC,
		)
	}

	// User and chat handlers are temporarily set to nil until implementation is complete
	// TODO: Initialize user and chat use cases and handlers
	// Uncomment when handlers are ready:
	// createUserUC := user.NewCreateUserUseCase(userRepo.(*database.PostgresUserRepository), quotaRepo, uowFactory)
	// userHandler := handlers.NewUserHandler(createUserUC, ...)
	// chatHandler := handlers.NewChatHandler(...)
	var userHandler *handlers.UserHandler = nil
	var chatHandler *handlers.ChatHandler = nil

	// Prevent unused variable warnings
	_ = userRepo
	_ = quotaRepo
	_ = uowFactory

	// Create Fiber app
	app := fiber.New(fiber.Config{
		ErrorHandler: func(c *fiber.Ctx, err error) error {
			logger.Error("Unhandled error", zap.Error(err))
			return c.Status(500).JSON(fiber.Map{"error": "Internal server error"})
		},
	})

	// Setup routes
	routes.SetupRoutes(app, agentHandler, userHandler, chatHandler)

	// Start server
	go func() {
		logger.Info("Starting server", zap.String("host", cfg.Server.Host), zap.Int("port", cfg.Server.Port))
		if err := app.Listen(fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)); err != nil {
			logger.Fatal("Failed to start server", zap.Error(err))
		}
	}()

	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	logger.Info("Shutting down server...")

	if err := app.Shutdown(); err != nil {
		logger.Fatal("Server forced to shutdown", zap.Error(err))
	}

	logger.Info("Server exited")
}
