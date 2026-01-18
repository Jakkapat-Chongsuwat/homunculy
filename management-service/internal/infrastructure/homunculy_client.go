// Package infrastructure provides Homunculy service client
package infrastructure

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// HomunculyClient handles communication with Homunculy service
type HomunculyClient struct {
	baseURL    string
	httpClient *http.Client
	apiKey     string // Service-to-service authentication
}

// NewHomunculyClient creates a new Homunculy client
func NewHomunculyClient(baseURL, apiKey string) *HomunculyClient {
	return &HomunculyClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		apiKey: apiKey,
	}
}

// AgentConfiguration represents agent configuration
type AgentConfiguration struct {
	Provider     string           `json:"provider"`
	ModelName    string           `json:"model_name"`
	SystemPrompt string           `json:"system_prompt"`
	Temperature  float64          `json:"temperature"`
	MaxTokens    int              `json:"max_tokens"`
	Personality  AgentPersonality `json:"personality"`
}

// AgentPersonality represents agent personality traits
type AgentPersonality struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Traits      map[string]interface{} `json:"traits"`
	Mood        string                 `json:"mood"`
}

// ExecuteChatRequest represents the request to execute chat
type ExecuteChatRequest struct {
	UserID        string                 `json:"user_id"`
	Message       string                 `json:"message"`
	Configuration AgentConfiguration     `json:"configuration"`
	Context       map[string]interface{} `json:"context"`
}

// ChatResponse represents the response from chat execution
type ChatResponse struct {
	Message    string  `json:"message"`
	Confidence float64 `json:"confidence"`
	Reasoning  string  `json:"reasoning"`
}

// ExecuteChat executes a chat with the provided configuration (stateless)
func (c *HomunculyClient) ExecuteChat(ctx context.Context, req *ExecuteChatRequest) (*ChatResponse, error) {
	url := fmt.Sprintf("%s/api/v1/agents/execute", c.baseURL)

	// Serialize request
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.apiKey))

	// Execute request
	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	// Read response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Check status code
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("homunculy returned error: %d - %s", resp.StatusCode, string(body))
	}

	// Parse response
	var chatResp ChatResponse
	if err := json.Unmarshal(body, &chatResp); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &chatResp, nil
}

// GetAgentFromHomunculy retrieves agent config from Homunculy (deprecated endpoint)
// This is for backward compatibility - should use GetAgentFromMongoDB instead
func (c *HomunculyClient) GetAgentFromHomunculy(ctx context.Context, agentID string) (*AgentConfiguration, error) {
	url := fmt.Sprintf("%s/api/v1/agents/%s", c.baseURL, agentID)

	httpReq, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.apiKey))

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("homunculy returned error: %d - %s", resp.StatusCode, string(body))
	}

	var config AgentConfiguration
	if err := json.NewDecoder(resp.Body).Decode(&config); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &config, nil
}

// JoinRoomRequest tells the agent to join a LiveKit room.
type JoinRoomRequest struct {
	Room     string                 `json:"room"`
	UserID   string                 `json:"user_id"`
	Metadata map[string]interface{} `json:"metadata"`
}

// JoinRoomResponse is the agent's response.
type JoinRoomResponse struct {
	SessionID string `json:"session_id"`
	Room      string `json:"room"`
	Status    string `json:"status"`
}

// JoinRoom tells the agent to join a room.
// This is the key - Management Service COMMANDS the agent.
// Agent decides to connect to LiveKit itself.
func (c *HomunculyClient) JoinRoom(ctx context.Context, req *JoinRoomRequest) (*JoinRoomResponse, error) {
	url := fmt.Sprintf("%s/join", c.baseURL)

	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.apiKey))

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to call agent join: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("agent join failed: %d - %s", resp.StatusCode, string(body))
	}

	var joinResp JoinRoomResponse
	if err := json.Unmarshal(body, &joinResp); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &joinResp, nil
}

// LeaveRoomRequest tells the agent to leave a room.
type LeaveRoomRequest struct {
	SessionID string `json:"session_id"`
}

// LeaveRoom tells the agent to leave a room.
func (c *HomunculyClient) LeaveRoom(ctx context.Context, sessionID string) error {
	url := fmt.Sprintf("%s/leave", c.baseURL)

	req := LeaveRoomRequest{SessionID: sessionID}
	jsonData, _ := json.Marshal(req)

	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("failed to call agent leave: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("agent leave failed: %d - %s", resp.StatusCode, string(body))
	}

	return nil
}
