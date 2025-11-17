-- name: CreateAgentAssignment :one
INSERT INTO agent_assignments (
    user_id, agent_id_reference, allocation_strategy, priority, max_concurrent_requests
)
VALUES ($1, $2, $3, $4, $5)
RETURNING *;

-- name: GetAgentAssignmentByID :one
SELECT * FROM agent_assignments
WHERE id = $1 LIMIT 1;

-- name: GetAgentAssignmentsByUserID :many
SELECT * FROM agent_assignments
WHERE user_id = $1
ORDER BY priority DESC;

-- name: GetAgentAssignmentsByAgentID :many
SELECT * FROM agent_assignments
WHERE agent_id_reference = $1;

-- name: DeleteAgentAssignment :exec
DELETE FROM agent_assignments
WHERE id = $1;

-- name: DeleteAgentAssignmentByUserAndAgent :exec
DELETE FROM agent_assignments
WHERE user_id = $1 AND agent_id_reference = $2;
