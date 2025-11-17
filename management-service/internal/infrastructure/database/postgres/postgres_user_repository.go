package postgres

import (
	"context"
	"fmt"

	"management-service/internal/domain/entities"
	"management-service/internal/infrastructure/database/sqlc"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jackc/pgx/v5/pgxpool"
)

// UserRepository implements user operations with PostgreSQL
type UserRepository struct {
	pool    *pgxpool.Pool
	queries *sqlc.Queries
}

// NewUserRepository creates a new PostgreSQL user repository
func NewUserRepository(pool *pgxpool.Pool) *UserRepository {
	return &UserRepository{
		pool:    pool,
		queries: sqlc.New(pool),
	}
}

// Create creates a new user
func (r *UserRepository) Create(ctx context.Context, user *entities.User) error {
	params := sqlc.CreateUserParams{
		Email:            user.Email,
		Name:             user.Name,
		SubscriptionTier: string(user.SubscriptionTier),
		IsActive:         user.IsActive,
	}

	dbUser, err := r.queries.CreateUser(ctx, params)
	if err != nil {
		return fmt.Errorf("failed to create user: %w", err)
	}

	// Map back to domain entity
	user.ID = uuidToString(dbUser.ID)
	user.CreatedAt = timestampToTime(dbUser.CreatedAt)
	user.UpdatedAt = timestampToTime(dbUser.UpdatedAt)

	return nil
}

// GetByID retrieves a user by ID
func (r *UserRepository) GetByID(ctx context.Context, id string) (*entities.User, error) {
	pgUUID, err := stringToUUID(id)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID: %w", err)
	}

	dbUser, err := r.queries.GetUserByID(ctx, pgUUID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user by ID: %w", err)
	}

	return mapToUserEntity(&dbUser), nil
}

// GetByEmail retrieves a user by email
func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*entities.User, error) {
	dbUser, err := r.queries.GetUserByEmail(ctx, email)
	if err != nil {
		return nil, fmt.Errorf("failed to get user by email: %w", err)
	}

	return mapToUserEntity(&dbUser), nil
}

// Update updates a user
func (r *UserRepository) Update(ctx context.Context, user *entities.User) error {
	pgUUID, err := stringToUUID(user.ID)
	if err != nil {
		return fmt.Errorf("invalid user ID: %w", err)
	}

	params := sqlc.UpdateUserParams{
		ID:               pgUUID,
		Email:            user.Email,
		Name:             user.Name,
		SubscriptionTier: string(user.SubscriptionTier),
		IsActive:         user.IsActive,
	}

	dbUser, err := r.queries.UpdateUser(ctx, params)
	if err != nil {
		return fmt.Errorf("failed to update user: %w", err)
	}

	// Update timestamps
	user.UpdatedAt = timestampToTime(dbUser.UpdatedAt)

	return nil
}

// Delete deletes a user
func (r *UserRepository) Delete(ctx context.Context, id string) error {
	pgUUID, err := stringToUUID(id)
	if err != nil {
		return fmt.Errorf("invalid user ID: %w", err)
	}

	if err := r.queries.DeleteUser(ctx, pgUUID); err != nil {
		return fmt.Errorf("failed to delete user: %w", err)
	}

	return nil
}

// List retrieves users with pagination
func (r *UserRepository) List(ctx context.Context, limit, offset int) ([]*entities.User, error) {
	params := sqlc.ListUsersParams{
		Limit:  int32(limit),
		Offset: int32(offset),
	}

	dbUsers, err := r.queries.ListUsers(ctx, params)
	if err != nil {
		return nil, fmt.Errorf("failed to list users: %w", err)
	}

	users := make([]*entities.User, len(dbUsers))
	for i, dbUser := range dbUsers {
		users[i] = mapToUserEntity(&dbUser)
	}

	return users, nil
}

// ListAll retrieves users with pagination (alias for List to implement interface)
func (r *UserRepository) ListAll(ctx context.Context, limit, offset int) ([]*entities.User, error) {
	return r.List(ctx, limit, offset)
}

// CreateWithQuerier creates a user using provided Querier (supports transactions)
func (r *UserRepository) CreateWithQuerier(ctx context.Context, q sqlc.Querier, user *entities.User) error {
	params := sqlc.CreateUserParams{
		Email:            user.Email,
		Name:             user.Name,
		SubscriptionTier: string(user.SubscriptionTier),
		IsActive:         user.IsActive,
	}

	dbUser, err := q.CreateUser(ctx, params)
	if err != nil {
		return fmt.Errorf("failed to create user: %w", err)
	}

	user.ID = uuidToString(dbUser.ID)
	user.CreatedAt = timestampToTime(dbUser.CreatedAt)
	user.UpdatedAt = timestampToTime(dbUser.UpdatedAt)

	return nil
}

// mapToUserEntity converts sqlc User to domain entity
func mapToUserEntity(dbUser *sqlc.User) *entities.User {
	return &entities.User{
		ID:               uuidToString(dbUser.ID),
		Email:            dbUser.Email,
		Name:             dbUser.Name,
		SubscriptionTier: entities.SubscriptionTier(dbUser.SubscriptionTier),
		IsActive:         dbUser.IsActive,
		CreatedAt:        timestampToTime(dbUser.CreatedAt),
		UpdatedAt:        timestampToTime(dbUser.UpdatedAt),
	}
}

// stringToUUID converts string to pgtype.UUID
func stringToUUID(s string) (pgtype.UUID, error) {
	var pgUUID pgtype.UUID
	id, err := uuid.Parse(s)
	if err != nil {
		return pgUUID, err
	}
	pgUUID.Bytes = id
	pgUUID.Valid = true
	return pgUUID, nil
}

// uuidToString converts pgtype.UUID to string
func uuidToString(pgUUID pgtype.UUID) string {
	if !pgUUID.Valid {
		return ""
	}
	return uuid.UUID(pgUUID.Bytes).String()
}
