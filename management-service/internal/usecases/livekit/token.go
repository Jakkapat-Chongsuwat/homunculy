package livekit

import (
	"context"

	"management-service/internal/domain/services"
)

// CreateTokenUseCase issues room tokens.
type CreateTokenUseCase struct {
	issuer     services.TokenIssuer
	defaultTtl int
}

// NewCreateTokenUseCase creates a new use case.
func NewCreateTokenUseCase(issuer services.TokenIssuer, defaultTtl int) *CreateTokenUseCase {
	return &CreateTokenUseCase{issuer: issuer, defaultTtl: defaultTtl}
}

// Execute issues a token for a room.
func (uc *CreateTokenUseCase) Execute(ctx context.Context, req CreateTokenRequest) (*CreateTokenResponse, error) {
	issue := toIssue(req, uc.defaultTtl)
	token, err := uc.issuer.IssueToken(ctx, issue)
	if err != nil {
		return nil, err
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
