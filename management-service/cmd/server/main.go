package main

import (
	"fmt"
	"log"
	"management-service/internal/adapters/http/handlers"
	"management-service/internal/adapters/http/routes"
	"management-service/internal/infrastructure/config"
	"management-service/internal/infrastructure/database"
	"management-service/internal/infrastructure/livekit"
	livekitusecase "management-service/internal/usecases/livekit"
	"os"
	"os/signal"
	"syscall"

	"github.com/gofiber/fiber/v2"
	"go.uber.org/zap"
)

func main() {
	logger := newLogger()
	defer logger.Sync()
	cfg := loadConfig(logger)
	dbFactory := newDbFactory(cfg, logger)
	defer closeDb(dbFactory, logger)
	initDb(dbFactory, logger)
	app := newApp(logger)
	setupRoutes(app, createLiveKitHandler(cfg))
	startServer(app, cfg, logger)
	awaitShutdown(app, logger)
}

func newLogger() *zap.Logger {
	logger, err := zap.NewProduction()
	if err != nil {
		log.Fatalf("Failed to initialize logger: %v", err)
	}
	return logger
}

func loadConfig(logger *zap.Logger) *config.Config {
	cfg := config.Load()
	logger.Info("Configuration loaded", zap.String("host", cfg.Server.Host), zap.Int("port", cfg.Server.Port))
	return cfg
}

func newDbFactory(cfg *config.Config, logger *zap.Logger) *database.DatabaseFactory {
	return database.NewDatabaseFactory(database.PostgreSQL, &cfg.Database, logger)
}

func closeDb(factory *database.DatabaseFactory, logger *zap.Logger) {
	if err := factory.Close(); err != nil {
		logger.Fatal("Failed to close database", zap.Error(err))
	}
}

func initDb(factory *database.DatabaseFactory, logger *zap.Logger) {
	if err := factory.Initialize(); err != nil {
		logger.Fatal("Failed to initialize database", zap.Error(err))
	}
}

func newApp(logger *zap.Logger) *fiber.App {
	return fiber.New(fiber.Config{ErrorHandler: errorHandler(logger)})
}

func errorHandler(logger *zap.Logger) fiber.ErrorHandler {
	return func(c *fiber.Ctx, err error) error {
		logger.Error("Unhandled error", zap.Error(err))
		return c.Status(500).JSON(fiber.Map{"error": "Internal server error"})
	}
}

func setupRoutes(app *fiber.App, livekitHandler *handlers.LiveKitHandler) {
	routes.SetupRoutes(app, nil, nil, nil, livekitHandler)
}

func startServer(app *fiber.App, cfg *config.Config, logger *zap.Logger) {
	go func() {
		logger.Info("Starting server", zap.String("host", cfg.Server.Host), zap.Int("port", cfg.Server.Port))
		if err := app.Listen(fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)); err != nil {
			logger.Fatal("Failed to start server", zap.Error(err))
		}
	}()
}

func awaitShutdown(app *fiber.App, logger *zap.Logger) {
	waitForSignal()
	shutdown(app, logger)
}

func waitForSignal() {
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
}

func shutdown(app *fiber.App, logger *zap.Logger) {
	logger.Info("Shutting down server...")
	if err := app.Shutdown(); err != nil {
		logger.Fatal("Server forced to shutdown", zap.Error(err))
	}
	logger.Info("Server exited")
}

func createLiveKitHandler(cfg *config.Config) *handlers.LiveKitHandler {
	issuer := tokenIssuer(cfg)
	if issuer == nil {
		return nil
	}
	agentJoiner := createAgentJoiner(cfg)
	return handlers.NewLiveKitHandler(tokenUseCase(issuer, agentJoiner, cfg))
}

func tokenIssuer(cfg *config.Config) *livekit.TokenIssuer {
	if missingLiveKit(cfg) {
		return nil
	}
	return livekit.NewTokenIssuer(cfg.LiveKit.APIKey, cfg.LiveKit.APISecret)
}

func missingLiveKit(cfg *config.Config) bool {
	return cfg.LiveKit.APIKey == "" || cfg.LiveKit.APISecret == ""
}

func createAgentJoiner(cfg *config.Config) *livekit.DispatchAgentJoiner {
	if missingLiveKit(cfg) {
		return nil
	}
	agentName := "homunculy-super" // Default agent name
	return livekit.NewDispatchAgentJoiner(cfg.LiveKit.Host, cfg.LiveKit.APIKey, cfg.LiveKit.APISecret, agentName)
}

func tokenUseCase(issuer *livekit.TokenIssuer, joiner *livekit.DispatchAgentJoiner, cfg *config.Config) *livekitusecase.CreateTokenUseCase {
	return livekitusecase.NewCreateTokenUseCase(issuer, joiner, cfg.LiveKit.TokenTTL)
}
