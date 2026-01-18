package livekit

import (
	"errors"
	"time"

	"github.com/livekit/protocol/auth"

	"management-service/internal/domain/services"
)

// TokenIssuer issues LiveKit room tokens.
// NO dispatch logic - agent controls itself via /join API.
type TokenIssuer struct {
	apiKey    string
	apiSecret string
}

// NewTokenIssuer creates a new issuer.
func NewTokenIssuer(apiKey, apiSecret string) *TokenIssuer {
	return &TokenIssuer{apiKey: apiKey, apiSecret: apiSecret}
}

// IssueToken issues a room token for a user.
// Agent is NOT dispatched here - Management Service calls agent /join separately.
func (i *TokenIssuer) IssueToken(req services.TokenIssueRequest) (string, error) {
	if err := validate(req, i.apiKey, i.apiSecret); err != nil {
		return "", err
	}
	return buildToken(i.apiKey, i.apiSecret, req)
}

func validate(req services.TokenIssueRequest, key, secret string) error {
	if key == "" || secret == "" {
		return errors.New("livekit credentials missing")
	}
	if req.Room == "" || req.Identity == "" {
		return errors.New("room and identity required")
	}
	return nil
}

func buildToken(key, secret string, req services.TokenIssueRequest) (string, error) {
	at := auth.NewAccessToken(key, secret)

	grant := &auth.VideoGrant{
		RoomJoin:       true,
		Room:           req.Room,
		CanPublish:     boolPtr(true),
		CanSubscribe:   boolPtr(true),
		CanPublishData: boolPtr(true),
	}

	at.SetIdentity(req.Identity)
	at.SetVideoGrant(grant)
	at.SetValidFor(time.Duration(req.TtlSeconds) * time.Second)
	if req.Metadata != "" {
		at.SetMetadata(req.Metadata)
	}

	return at.ToJWT()
}

func boolPtr(value bool) *bool {
	return &value
}
