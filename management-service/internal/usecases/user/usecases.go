package user

import (
	"context"
	"fmt"
	"time"

	"management-service/internal/domain/entities"
	"management-service/internal/domain/repositories"
	"management-service/internal/infrastructure"
	"management-service/internal/infrastructure/database"
	"management-service/internal/infrastructure/database/postgres"
)

// CreateUserUseCase handles user creation
type CreateUserUseCase struct {
	userRepo   *postgres.UserRepository
	quotaRepo  *postgres.QuotaRepository
	uowFactory func(ctx context.Context) (database.UnitOfWork, error)
}

// NewCreateUserUseCase creates a new CreateUserUseCase
func NewCreateUserUseCase(
	userRepo *postgres.UserRepository,
	quotaRepo *postgres.QuotaRepository,
	uowFactory func(ctx context.Context) (database.UnitOfWork, error),
) *CreateUserUseCase {
	return &CreateUserUseCase{
		userRepo:   userRepo,
		quotaRepo:  quotaRepo,
		uowFactory: uowFactory,
	}
}

// Execute creates a new user with default quota in a transaction
func (uc *CreateUserUseCase) Execute(ctx context.Context, email, name string, subscriptionTier entities.SubscriptionTier) (*entities.User, error) {
	// Start transaction
	uow, err := uc.uowFactory(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to create unit of work: %w", err)
	}
	defer uow.Rollback(ctx)

	// Create user
	user := &entities.User{
		Email:            email,
		Name:             name,
		SubscriptionTier: subscriptionTier,
		IsActive:         true,
	}

	if err := uc.userRepo.CreateWithQuerier(ctx, uow.Queries(), user); err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	// Set default quota based on subscription tier
	quota := &entities.Quota{
		UserID:               user.ID,
		Tier:                 subscriptionTier,
		MaxAgents:            getMaxAgentsForTier(subscriptionTier),
		MaxTokensPerDay:      int64(getMaxTokensForTier(subscriptionTier)),
		MaxRequestsPerDay:    getMaxRequestsForTier(subscriptionTier),
		MaxRequestsPerMinute: getMaxRequestsPerMinuteForTier(subscriptionTier),
		UsedTokensToday:      0,
		UsedRequestsToday:    0,
		ResetDate:            time.Now().AddDate(0, 0, 1),
	}

	if err := uc.quotaRepo.CreateWithQuerier(ctx, uow.Queries(), quota); err != nil {
		return nil, fmt.Errorf("failed to create quota: %w", err)
	}

	// Commit transaction
	if err := uow.Commit(ctx); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return user, nil
}

// getMaxTokensForTier returns max tokens based on subscription tier
func getMaxTokensForTier(tier entities.SubscriptionTier) int {
	switch tier {
	case entities.SubscriptionTierFree:
		return 10000 // 10k tokens per day
	case entities.SubscriptionTierPremium:
		return 100000 // 100k tokens per day
	case entities.SubscriptionTierEnterprise:
		return 1000000 // 1M tokens per day
	default:
		return 10000
	}
}

// getMaxAgentsForTier returns max agents based on subscription tier
func getMaxAgentsForTier(tier entities.SubscriptionTier) int32 {
	switch tier {
	case entities.SubscriptionTierFree:
		return 1 // 1 agent
	case entities.SubscriptionTierPremium:
		return 5 // 5 agents
	case entities.SubscriptionTierEnterprise:
		return 50 // 50 agents
	default:
		return 1
	}
}

// getMaxRequestsForTier returns max requests based on subscription tier
func getMaxRequestsForTier(tier entities.SubscriptionTier) int32 {
	switch tier {
	case entities.SubscriptionTierFree:
		return 100 // 100 requests per day
	case entities.SubscriptionTierPremium:
		return 1000 // 1k requests per day
	case entities.SubscriptionTierEnterprise:
		return 10000 // 10k requests per day
	default:
		return 100
	}
}

// getMaxRequestsPerMinuteForTier returns max requests per minute based on subscription tier
func getMaxRequestsPerMinuteForTier(tier entities.SubscriptionTier) int32 {
	switch tier {
	case entities.SubscriptionTierFree:
		return 10 // 10 RPM
	case entities.SubscriptionTierPremium:
		return 60 // 60 RPM
	case entities.SubscriptionTierEnterprise:
		return 300 // 300 RPM
	default:
		return 10
	}
}

// AssignAgentToUserUseCase handles agent assignment
type AssignAgentToUserUseCase struct {
	assignmentRepo repositories.AssignmentRepository
}

// NewAssignAgentToUserUseCase creates a new AssignAgentToUserUseCase
func NewAssignAgentToUserUseCase(assignmentRepo repositories.AssignmentRepository) *AssignAgentToUserUseCase {
	return &AssignAgentToUserUseCase{
		assignmentRepo: assignmentRepo,
	}
}

// Execute assigns an agent to a user
func (uc *AssignAgentToUserUseCase) Execute(ctx context.Context, userID, agentIDReference string, strategy entities.AllocationStrategy) (*entities.AgentAssignment, error) {
	assignment := &entities.AgentAssignment{
		UserID:             userID,
		AgentIDReference:   agentIDReference,
		AllocationStrategy: strategy,
	}

	if err := uc.assignmentRepo.Create(ctx, assignment); err != nil {
		return nil, fmt.Errorf("failed to assign agent: %w", err)
	}

	return assignment, nil
}

// CheckUserQuotaUseCase handles quota checking
type CheckUserQuotaUseCase struct {
	quotaRepo repositories.QuotaRepository
}

// NewCheckUserQuotaUseCase creates a new CheckUserQuotaUseCase
func NewCheckUserQuotaUseCase(quotaRepo repositories.QuotaRepository) *CheckUserQuotaUseCase {
	return &CheckUserQuotaUseCase{
		quotaRepo: quotaRepo,
	}
}

// Execute checks if user has quota available
func (uc *CheckUserQuotaUseCase) Execute(ctx context.Context, userID string, tokensRequired int) (bool, error) {
	quota, err := uc.quotaRepo.GetByUserID(ctx, userID)
	if err != nil {
		return false, fmt.Errorf("failed to get quota: %w", err)
	}

	// Check if user has enough tokens
	if int64(quota.UsedTokensToday+int32(tokensRequired)) > quota.MaxTokensPerDay {
		return false, nil
	}

	// Check if user has exceeded request limit
	if quota.UsedRequestsToday >= quota.MaxRequestsPerDay {
		return false, nil
	}

	return true, nil
}

// TrackUsageUseCase handles usage tracking
type TrackUsageUseCase struct {
	usageRepo repositories.UsageRepository
	quotaRepo repositories.QuotaRepository
}

// NewTrackUsageUseCase creates a new TrackUsageUseCase
func NewTrackUsageUseCase(
	usageRepo repositories.UsageRepository,
	quotaRepo repositories.QuotaRepository,
) *TrackUsageUseCase {
	return &TrackUsageUseCase{
		usageRepo: usageRepo,
		quotaRepo: quotaRepo,
	}
}

// Execute tracks usage for a user
func (uc *TrackUsageUseCase) Execute(ctx context.Context, userID, agentID string, tokensUsed int, cost float64) error {
	// Create usage metric
	metric := &entities.UsageMetric{
		UserID:           userID,
		AgentIDReference: agentID,
		TokensUsed:       int64(tokensUsed),
		RequestsCount:    1,
		Cost:             cost,
	}

	if err := uc.usageRepo.Create(ctx, metric); err != nil {
		return fmt.Errorf("failed to create usage metric: %w", err)
	}

	// Update quota
	quota, err := uc.quotaRepo.GetByUserID(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get quota: %w", err)
	}

	quota.UsedTokensToday += int32(tokensUsed)
	quota.UsedRequestsToday++

	if err := uc.quotaRepo.Update(ctx, quota); err != nil {
		return fmt.Errorf("failed to update quota: %w", err)
	}

	return nil
}

// ExecuteChatUseCase orchestrates chat execution with Homunculy
type ExecuteChatUseCase struct {
	assignmentRepo  repositories.AssignmentRepository
	quotaUseCase    *CheckUserQuotaUseCase
	trackUseCase    *TrackUsageUseCase
	homunculyClient *infrastructure.HomunculyClient
}

// NewExecuteChatUseCase creates a new ExecuteChatUseCase
func NewExecuteChatUseCase(
	assignmentRepo repositories.AssignmentRepository,
	quotaUseCase *CheckUserQuotaUseCase,
	trackUseCase *TrackUsageUseCase,
	homunculyClient *infrastructure.HomunculyClient,
) *ExecuteChatUseCase {
	return &ExecuteChatUseCase{
		assignmentRepo:  assignmentRepo,
		quotaUseCase:    quotaUseCase,
		trackUseCase:    trackUseCase,
		homunculyClient: homunculyClient,
	}
}

// Execute executes a chat request
func (uc *ExecuteChatUseCase) Execute(ctx context.Context, userID, message string, agentConfig infrastructure.AgentConfiguration) (*infrastructure.ChatResponse, error) {
	// Check quota
	estimatedTokens := len(message) / 4 // Rough estimate: 1 token ~= 4 chars
	hasQuota, err := uc.quotaUseCase.Execute(ctx, userID, estimatedTokens)
	if err != nil {
		return nil, fmt.Errorf("failed to check quota: %w", err)
	}

	if !hasQuota {
		return nil, fmt.Errorf("quota exceeded for user %s", userID)
	}

	// Execute chat with Homunculy
	req := &infrastructure.ExecuteChatRequest{
		UserID:        userID,
		Message:       message,
		Configuration: agentConfig,
		Context:       make(map[string]interface{}),
	}

	response, err := uc.homunculyClient.ExecuteChat(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute chat: %w", err)
	}

	// Track usage (tokens from response + request)
	totalTokens := estimatedTokens + len(response.Message)/4
	cost := calculateCost(totalTokens)

	if err := uc.trackUseCase.Execute(ctx, userID, agentConfig.Provider, totalTokens, cost); err != nil {
		// Log error but don't fail the request
		fmt.Printf("Failed to track usage: %v\n", err)
	}

	return response, nil
}

// calculateCost calculates cost based on tokens used
func calculateCost(tokens int) float64 {
	// Simple cost model: $0.002 per 1000 tokens (GPT-4 pricing)
	return float64(tokens) / 1000.0 * 0.002
}
