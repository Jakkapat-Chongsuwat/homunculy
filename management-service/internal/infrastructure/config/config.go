package config

import (
	"os"
	"strconv"
	"time"
)

// Config holds all configuration for the application
type Config struct {
	Server   ServerConfig
	Database DatabaseConfig
	Logging  LoggingConfig
	LiveKit  LiveKitConfig
}

// ServerConfig holds server-related configuration
type ServerConfig struct {
	Host         string        `json:"host"`
	Port         int           `json:"port"`
	ReadTimeout  time.Duration `json:"read_timeout"`
	WriteTimeout time.Duration `json:"write_timeout"`
}

// DatabaseConfig holds database-related configuration
type DatabaseConfig struct {
	Host           string `json:"host"`
	Port           int    `json:"port"`
	Database       string `json:"database"`
	User           string `json:"user"`
	Password       string `json:"password"`
	SSLMode        string `json:"ssl_mode"`
	MaxConnections int    `json:"max_connections"`
}

// LoggingConfig holds logging-related configuration
type LoggingConfig struct {
	Level  string `json:"level"`
	Format string `json:"format"`
}

// LiveKitConfig holds LiveKit settings.
type LiveKitConfig struct {
	APIKey    string `json:"api_key"`
	APISecret string `json:"api_secret"`
	TokenTTL  int    `json:"token_ttl"`
}

// Load loads configuration from environment variables with defaults
func Load() *Config {
	return &Config{
		Server: ServerConfig{
			Host:         getEnv("SERVER_HOST", "0.0.0.0"),
			Port:         getEnvAsInt("SERVER_PORT", 8080),
			ReadTimeout:  getEnvAsDuration("SERVER_READ_TIMEOUT", 15*time.Second),
			WriteTimeout: getEnvAsDuration("SERVER_WRITE_TIMEOUT", 15*time.Second),
		},
		Database: DatabaseConfig{
			Host:           getEnv("DB_HOST", "localhost"),
			Port:           getEnvAsInt("DB_PORT", 5434),
			Database:       getEnv("DB_NAME", "management_service"),
			User:           getEnv("DB_USER", "postgres"),
			Password:       getEnv("DB_PASSWORD", "postgres"),
			SSLMode:        getEnv("DB_SSL_MODE", "disable"),
			MaxConnections: getEnvAsInt("DB_MAX_CONNECTIONS", 25),
		},
		Logging: LoggingConfig{
			Level:  getEnv("LOG_LEVEL", "info"),
			Format: getEnv("LOG_FORMAT", "json"),
		},
		LiveKit: LiveKitConfig{
			APIKey:    getEnv("LIVEKIT_API_KEY", ""),
			APISecret: getEnv("LIVEKIT_API_SECRET", ""),
			TokenTTL:  getEnvAsInt("LIVEKIT_TOKEN_TTL", 3600),
		},
	}
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvAsInt gets an environment variable as int or returns a default value
func getEnvAsInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

// getEnvAsDuration gets an environment variable as duration or returns a default value
func getEnvAsDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}
