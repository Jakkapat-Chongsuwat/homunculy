package postgres

import (
	"context"
	"fmt"
	"time"

	"management-service/internal/domain/entities"
	"management-service/internal/infrastructure/database/sqlc"

	"github.com/jackc/pgx/v5/pgxpool"
)

// QuotaRepository implements quota operations with PostgreSQL
type QuotaRepository struct {
	pool    *pgxpool.Pool
	queries *sqlc.Queries
}

// NewQuotaRepository creates a new PostgreSQL quota repository
func NewQuotaRepository(pool *pgxpool.Pool) *QuotaRepository {
	return &QuotaRepository{
		pool:    pool,
		queries: sqlc.New(pool),
	}
}

// Create creates a new quota
func (r *QuotaRepository) Create(ctx context.Context, quota *entities.Quota) error {
	userUUID, err := stringToUUID(quota.UserID)
	if err != nil {
		return fmt.Errorf("invalid user ID: %w", err)
	}

	params := sqlc.CreateQuotaParams{
		UserID:               userUUID,
		Tier:                 string(quota.Tier),
		MaxAgents:            quota.MaxAgents,
		MaxTokensPerDay:      quota.MaxTokensPerDay,
		MaxRequestsPerDay:    quota.MaxRequestsPerDay,
		MaxRequestsPerMinute: quota.MaxRequestsPerMinute,
		UsedTokensToday:      quota.UsedTokensToday,
		UsedRequestsToday:    quota.UsedRequestsToday,
		ResetDate:            timeToTimestamp(quota.ResetDate),
	}

	dbQuota, err := r.queries.CreateQuota(ctx, params)
	if err != nil {
		return fmt.Errorf("failed to create quota: %w", err)
	}

	quota.ID = uuidToString(dbQuota.ID)
	quota.CreatedAt = timestampToTime(dbQuota.CreatedAt)
	quota.UpdatedAt = timestampToTime(dbQuota.UpdatedAt)

	return nil
}

// GetByUserID retrieves a quota by user ID
func (r *QuotaRepository) GetByUserID(ctx context.Context, userID string) (*entities.Quota, error) {
	userUUID, err := stringToUUID(userID)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID: %w", err)
	}

	dbQuota, err := r.queries.GetQuotaByUserID(ctx, userUUID)
	if err != nil {
		return nil, fmt.Errorf("failed to get quota by user ID: %w", err)
	}

	return mapToQuotaEntity(&dbQuota), nil
}

// Update updates a quota (only updates used tokens and requests)
func (r *QuotaRepository) Update(ctx context.Context, quota *entities.Quota) error {
	userUUID, err := stringToUUID(quota.UserID)
	if err != nil {
		return fmt.Errorf("invalid user ID: %w", err)
	}

	params := sqlc.UpdateQuotaParams{
		UserID:            userUUID,
		UsedTokensToday:   quota.UsedTokensToday,
		UsedRequestsToday: quota.UsedRequestsToday,
	}

	dbQuota, err := r.queries.UpdateQuota(ctx, params)
	if err != nil {
		return fmt.Errorf("failed to update quota: %w", err)
	}

	quota.UpdatedAt = timestampToTime(dbQuota.UpdatedAt)

	return nil
}

// Delete deletes a quota
func (r *QuotaRepository) Delete(ctx context.Context, userID string) error {
	userUUID, err := stringToUUID(userID)
	if err != nil {
		return fmt.Errorf("invalid user ID: %w", err)
	}

	if err := r.queries.DeleteQuota(ctx, userUUID); err != nil {
		return fmt.Errorf("failed to delete quota: %w", err)
	}

	return nil
}

// ResetDaily resets all daily quotas
func (r *QuotaRepository) ResetDaily(ctx context.Context, resetDate time.Time) error {
	if err := r.queries.ResetDailyQuota(ctx, timeToTimestamp(resetDate)); err != nil {
		return fmt.Errorf("failed to reset daily quotas: %w", err)
	}

	return nil
}

// CreateWithQuerier creates a quota using provided Querier (supports transactions)
func (r *QuotaRepository) CreateWithQuerier(ctx context.Context, q sqlc.Querier, quota *entities.Quota) error {
	userUUID, err := stringToUUID(quota.UserID)
	if err != nil {
		return fmt.Errorf("invalid user ID: %w", err)
	}

	params := sqlc.CreateQuotaParams{
		UserID:               userUUID,
		Tier:                 string(quota.Tier),
		MaxAgents:            quota.MaxAgents,
		MaxTokensPerDay:      quota.MaxTokensPerDay,
		MaxRequestsPerDay:    quota.MaxRequestsPerDay,
		MaxRequestsPerMinute: quota.MaxRequestsPerMinute,
		UsedTokensToday:      quota.UsedTokensToday,
		UsedRequestsToday:    quota.UsedRequestsToday,
		ResetDate:            timeToTimestamp(quota.ResetDate),
	}

	dbQuota, err := q.CreateQuota(ctx, params)
	if err != nil {
		return fmt.Errorf("failed to create quota: %w", err)
	}

	quota.ID = uuidToString(dbQuota.ID)
	quota.CreatedAt = timestampToTime(dbQuota.CreatedAt)
	quota.UpdatedAt = timestampToTime(dbQuota.UpdatedAt)

	return nil
}

// UpdateWithQuerier updates a quota using provided Querier (supports transactions)
func (r *QuotaRepository) UpdateWithQuerier(ctx context.Context, q sqlc.Querier, quota *entities.Quota) error {
	userUUID, err := stringToUUID(quota.UserID)
	if err != nil {
		return fmt.Errorf("invalid user ID: %w", err)
	}

	params := sqlc.UpdateQuotaParams{
		UserID:            userUUID,
		UsedTokensToday:   quota.UsedTokensToday,
		UsedRequestsToday: quota.UsedRequestsToday,
	}

	dbQuota, err := q.UpdateQuota(ctx, params)
	if err != nil {
		return fmt.Errorf("failed to update quota: %w", err)
	}

	quota.UpdatedAt = timestampToTime(dbQuota.UpdatedAt)

	return nil
}

// mapToQuotaEntity converts sqlc Quota to domain entity
func mapToQuotaEntity(dbQuota *sqlc.Quota) *entities.Quota {
	return &entities.Quota{
		ID:                   uuidToString(dbQuota.ID),
		UserID:               uuidToString(dbQuota.UserID),
		Tier:                 entities.SubscriptionTier(dbQuota.Tier),
		MaxAgents:            dbQuota.MaxAgents,
		MaxTokensPerDay:      dbQuota.MaxTokensPerDay,
		MaxRequestsPerDay:    dbQuota.MaxRequestsPerDay,
		MaxRequestsPerMinute: dbQuota.MaxRequestsPerMinute,
		UsedTokensToday:      dbQuota.UsedTokensToday,
		UsedRequestsToday:    dbQuota.UsedRequestsToday,
		ResetDate:            timestampToTime(dbQuota.ResetDate),
		CreatedAt:            timestampToTime(dbQuota.CreatedAt),
		UpdatedAt:            timestampToTime(dbQuota.UpdatedAt),
	}
}
