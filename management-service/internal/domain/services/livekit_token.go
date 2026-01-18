package services

// TokenIssuer issues LiveKit access tokens.
type TokenIssuer interface {
	IssueToken(req TokenIssueRequest) (string, error)
}

// TokenIssueRequest is the input for token issuance.
type TokenIssueRequest struct {
	Room       string
	Identity   string
	Metadata   string
	TtlSeconds int
}

// AgentJoiner tells the agent to join a room.
// Management Service uses this to command the agent.
type AgentJoiner interface {
	JoinRoom(room, userID string, metadata map[string]interface{}) (sessionID string, err error)
	LeaveRoom(sessionID string) error
}
