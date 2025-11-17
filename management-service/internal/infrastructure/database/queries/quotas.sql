-- name: CreateQuota :one
INSERT INTO quotas (
    user_id, tier, max_agents, max_tokens_per_day, max_requests_per_day,
    max_requests_per_minute, used_tokens_today, used_requests_today, reset_date
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
RETURNING *;

-- name: GetQuotaByUserID :one
SELECT * FROM quotas
WHERE user_id = $1 LIMIT 1;

-- name: UpdateQuota :one
UPDATE quotas
SET used_tokens_today = $2, used_requests_today = $3, updated_at = CURRENT_TIMESTAMP
WHERE user_id = $1
RETURNING *;

-- name: ResetDailyQuota :exec
UPDATE quotas
SET used_tokens_today = 0, used_requests_today = 0, reset_date = $1
WHERE reset_date < CURRENT_TIMESTAMP;

-- name: DeleteQuota :exec
DELETE FROM quotas
WHERE user_id = $1;
