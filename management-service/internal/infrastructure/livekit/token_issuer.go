package livekit

import (
	"context"
	"errors"
	"time"

	"github.com/livekit/protocol/auth"

	"management-service/internal/domain/services"
)

// TokenIssuer issues LiveKit room tokens.
type TokenIssuer struct {
	apiKey    string
	apiSecret string
}

// NewTokenIssuer creates a new issuer.
func NewTokenIssuer(apiKey, apiSecret string) *TokenIssuer {
	return &TokenIssuer{apiKey: apiKey, apiSecret: apiSecret}
}

// IssueToken issues a room token.
func (i *TokenIssuer) IssueToken(ctx context.Context, req services.TokenIssueRequest) (string, error) {
	if err := validate(req, i.apiKey, i.apiSecret); err != nil {
		return "", err
	}
	return buildToken(i.apiKey, i.apiSecret, req)
}

func validate(req services.TokenIssueRequest, key, secret string) error {
	if key == "" || secret == "" {
		return errors.New("livekit credentials missing")
	}
	return validateRoom(req)
}

func validateRoom(req services.TokenIssueRequest) error {
	if req.Room == "" || req.Identity == "" {
		return errors.New("room and identity required")
	}
	return nil
}

func buildToken(key, secret string, req services.TokenIssueRequest) (string, error) {
	at := auth.NewAccessToken(key, secret)
	grant := roomGrant(req.Room)
	apply(at, req, grant)
	return at.ToJWT()
}

func roomGrant(room string) *auth.VideoGrant {
	return &auth.VideoGrant{
		RoomJoin:       true,
		Room:           room,
		CanPublish:     boolPtr(true),
		CanSubscribe:   boolPtr(true),
		CanPublishData: boolPtr(true),
	}
}

func boolPtr(value bool) *bool {
	return &value
}

func apply(at *auth.AccessToken, req services.TokenIssueRequest, grant *auth.VideoGrant) {
	at.SetIdentity(req.Identity)
	at.SetVideoGrant(grant)
	at.SetValidFor(time.Duration(req.TtlSeconds) * time.Second)
	if req.Metadata != "" {
		at.SetMetadata(req.Metadata)
	}
}
