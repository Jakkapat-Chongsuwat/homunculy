-- name: CreateUsageMetric :one
INSERT INTO usage_metrics (user_id, agent_id_reference, tokens_used, requests_count, cost)
VALUES ($1, $2, $3, $4, $5)
RETURNING *;

-- name: GetUsageMetricsByUserID :many
SELECT * FROM usage_metrics
WHERE user_id = $1
ORDER BY timestamp DESC
LIMIT $2;

-- name: GetUsageMetricsByUserIDAndDateRange :many
SELECT * FROM usage_metrics
WHERE user_id = $1
  AND timestamp >= $2
  AND timestamp <= $3
ORDER BY timestamp DESC;

-- name: GetTotalUsageByUser :one
SELECT
    user_id,
    SUM(tokens_used) as total_tokens_used,
    SUM(requests_count) as total_requests_count,
    SUM(cost) as total_cost
FROM usage_metrics
WHERE user_id = $1
GROUP BY user_id;
