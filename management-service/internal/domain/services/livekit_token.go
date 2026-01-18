package services

import "context"

// TokenIssuer issues LiveKit access tokens.
type TokenIssuer interface {
	IssueToken(ctx context.Context, req TokenIssueRequest) (string, error)
}

// TokenIssueRequest is the input for token issuance.
type TokenIssueRequest struct {
	Room       string
	Identity   string
	Metadata   string
	TtlSeconds int
}
