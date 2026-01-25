package livekit

import (
	"context"
	"encoding/json"
	"time"

	"github.com/livekit/protocol/livekit"
	lksdk "github.com/livekit/server-sdk-go/v2"
)

type DispatchAgentJoiner struct {
	roomClient     *lksdk.RoomServiceClient
	dispatchClient *lksdk.AgentDispatchClient
	agentName      string
}

// NewDispatchAgentJoiner creates a new dispatch-based agent joiner.
func NewDispatchAgentJoiner(host, apiKey, apiSecret, agentName string) *DispatchAgentJoiner {
	roomClient := lksdk.NewRoomServiceClient(host, apiKey, apiSecret)
	dispatchClient := lksdk.NewAgentDispatchServiceClient(host, apiKey, apiSecret)
	return &DispatchAgentJoiner{
		roomClient:     roomClient,
		dispatchClient: dispatchClient,
		agentName:      agentName,
	}
}

func (j *DispatchAgentJoiner) JoinRoom(room, userID string, metadata map[string]interface{}) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	_, err := j.roomClient.CreateRoom(ctx, &livekit.CreateRoomRequest{
		Name: room,
	})
	if err != nil && !isRoomExistsError(err) {
		return "", err
	}

	metaJSON := ""
	if metadata != nil {
		bytes, err := json.Marshal(metadata)
		if err == nil {
			metaJSON = string(bytes)
		}
	}

	dispatch, err := j.dispatchClient.CreateDispatch(ctx, &livekit.CreateAgentDispatchRequest{
		AgentName: j.agentName,
		Room:      room,
		Metadata:  metaJSON,
	})
	if err != nil {
		return "", err
	}

	return dispatch.Id, nil
}

func (j *DispatchAgentJoiner) LeaveRoom(sessionID string) error {
	return nil
}

func isRoomExistsError(err error) bool {
	return err != nil && (err.Error() == "room already exists" ||
		err.Error() == "room with that name already exists")
}
