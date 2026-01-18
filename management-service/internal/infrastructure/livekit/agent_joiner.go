package livekit

import (
	"context"
	"time"

	"management-service/internal/infrastructure"
)

// AgentJoiner implements services.AgentJoiner using HomunculyClient.
// This is how Management Service commands the agent to join rooms.
type AgentJoiner struct {
	client *infrastructure.HomunculyClient
}

// NewAgentJoiner creates a new agent joiner.
func NewAgentJoiner(client *infrastructure.HomunculyClient) *AgentJoiner {
	return &AgentJoiner{client: client}
}

// JoinRoom tells the agent to join a room.
// Agent will create its own token and connect to LiveKit.
func (j *AgentJoiner) JoinRoom(room, userID string, metadata map[string]interface{}) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	resp, err := j.client.JoinRoom(ctx, &infrastructure.JoinRoomRequest{
		Room:     room,
		UserID:   userID,
		Metadata: metadata,
	})
	if err != nil {
		return "", err
	}

	return resp.SessionID, nil
}

// LeaveRoom tells the agent to leave a room.
func (j *AgentJoiner) LeaveRoom(sessionID string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	return j.client.LeaveRoom(ctx, sessionID)
}
