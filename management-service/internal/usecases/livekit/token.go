package livekit

import (
	"context"
	"encoding/json"

	"management-service/internal/domain/services"
)

// CreateTokenUseCase issues room tokens AND tells agent to join.
// This is the Control Plane - it orchestrates the whole flow.
type CreateTokenUseCase struct {
	issuer      services.TokenIssuer
	agentJoiner services.AgentJoiner
	defaultTtl  int
}

// NewCreateTokenUseCase creates a new use case.
func NewCreateTokenUseCase(issuer services.TokenIssuer, agentJoiner services.AgentJoiner, defaultTtl int) *CreateTokenUseCase {
	return &CreateTokenUseCase{issuer: issuer, agentJoiner: agentJoiner, defaultTtl: defaultTtl}
}

// Execute issues a token and tells agent to join.
// Flow: 1) Create user token  2) Tell agent to join room  3) Return token
func (uc *CreateTokenUseCase) Execute(ctx context.Context, req CreateTokenRequest) (*CreateTokenResponse, error) {
	// 1. Issue token for user
	issue := toIssue(req, uc.defaultTtl)
	token, err := uc.issuer.IssueToken(issue)
	if err != nil {
		return nil, err
	}

	// 2. Tell agent to join room (agent controls itself)
	if uc.agentJoiner != nil {
		metadata := parseMetadata(req.Metadata)
		_, err = uc.agentJoiner.JoinRoom(req.Room, req.Identity, metadata)
		if err != nil {
			// Log but don't fail - user can still connect
			// TODO: proper logging
		}
	}

	return &CreateTokenResponse{Token: token, Room: req.Room, Identity: req.Identity}, nil
}

// CreateTokenRequest is the input DTO.
type CreateTokenRequest struct {
	Room       string `json:"room"`
	Identity   string `json:"identity"`
	Metadata   string `json:"metadata"`
	TtlSeconds int    `json:"ttl"`
}

// CreateTokenResponse is the output DTO.
type CreateTokenResponse struct {
	Token    string `json:"token"`
	Room     string `json:"room"`
	Identity string `json:"identity"`
}

func toIssue(req CreateTokenRequest, ttl int) services.TokenIssueRequest {
	return services.TokenIssueRequest{
		Room:       req.Room,
		Identity:   req.Identity,
		Metadata:   req.Metadata,
		TtlSeconds: pickTtl(req.TtlSeconds, ttl),
	}
}

func pickTtl(value, fallback int) int {
	if value > 0 {
		return value
	}
	return fallback
}

func parseMetadata(meta string) map[string]interface{} {
	if meta == "" {
		return nil
	}
	var result map[string]interface{}
	json.Unmarshal([]byte(meta), &result)
	return result
}
