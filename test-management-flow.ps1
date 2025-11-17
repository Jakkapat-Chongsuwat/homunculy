# Test Management Service API Flow
# This script tests the complete flow: User Creation → Agent Assignment → Chat Execution

Write-Host "=== Testing Management Service & Homunculy Integration ===" -ForegroundColor Cyan
Write-Host ""

# Base URLs
$managementUrl = "http://localhost:8080/api/v1"
$homunculyUrl = "http://localhost:8000"

# Test 1: Create a new user
Write-Host "1. Creating new user..." -ForegroundColor Yellow
$createUserBody = @{
    email = "test@example.com"
    name = "Test User"
    subscription_tier = "premium"
} | ConvertTo-Json

try {
    $userResponse = Invoke-RestMethod -Uri "$managementUrl/users" -Method Post -Body $createUserBody -ContentType "application/json"
    Write-Host "✓ User created successfully" -ForegroundColor Green
    Write-Host "  User ID: $($userResponse.id)" -ForegroundColor Gray
    Write-Host "  Email: $($userResponse.email)" -ForegroundColor Gray
    Write-Host "  Quota - Max Tokens: $($userResponse.quota.max_tokens_per_day)" -ForegroundColor Gray
    $userId = $userResponse.id
} catch {
    Write-Host "✗ Failed to create user: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Note: This endpoint is not implemented yet" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 2: Get user quota
Write-Host "2. Checking user quota..." -ForegroundColor Yellow
try {
    $quotaResponse = Invoke-RestMethod -Uri "$managementUrl/users/$userId/quota" -Method Get
    Write-Host "✓ Quota retrieved successfully" -ForegroundColor Green
    Write-Host "  Available Tokens: $($quotaResponse.available_tokens)" -ForegroundColor Gray
    Write-Host "  Available Requests: $($quotaResponse.available_requests)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to get quota: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Note: This endpoint is not implemented yet" -ForegroundColor Yellow
}

Write-Host ""

# Test 3: Create agent configuration via Management Service
Write-Host "3. Creating agent configuration..." -ForegroundColor Yellow
$agentConfig = @{
    name = "Customer Support Bot"
    provider = "langraph"
    model = "gpt-4"
    temperature = 0.7
    system_message = "You are a helpful customer support assistant."
    max_tokens = 1000
} | ConvertTo-Json

try {
    $agentResponse = Invoke-RestMethod -Uri "$managementUrl/agents" -Method Post -Body $agentConfig -ContentType "application/json"
    Write-Host "✓ Agent created successfully" -ForegroundColor Green
    Write-Host "  Agent ID: $($agentResponse.id)" -ForegroundColor Gray
    $agentId = $agentResponse.id
} catch {
    Write-Host "✗ Failed to create agent: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Note: This endpoint is not implemented yet" -ForegroundColor Yellow
}

Write-Host ""

# Test 4: Assign agent to user
Write-Host "4. Assigning agent to user..." -ForegroundColor Yellow
$assignmentBody = @{
    agent_id = $agentId
    allocation_strategy = "round_robin"
    priority = 1
} | ConvertTo-Json

try {
    $assignResponse = Invoke-RestMethod -Uri "$managementUrl/users/$userId/agents" -Method Post -Body $assignmentBody -ContentType "application/json"
    Write-Host "✓ Agent assigned successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to assign agent: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Note: This endpoint is not implemented yet" -ForegroundColor Yellow
}

Write-Host ""

# Test 5: Execute chat through Management Service
Write-Host "5. Executing chat request..." -ForegroundColor Yellow
$chatBody = @{
    user_id = $userId
    message = "Hello! Can you help me with my order?"
    agent_id = $agentId
} | ConvertTo-Json

try {
    $chatResponse = Invoke-RestMethod -Uri "$managementUrl/chat" -Method Post -Body $chatBody -ContentType "application/json"
    Write-Host "✓ Chat executed successfully" -ForegroundColor Green
    Write-Host "  Response: $($chatResponse.message)" -ForegroundColor Gray
    Write-Host "  Tokens Used: $($chatResponse.tokens_used)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to execute chat: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Note: This endpoint is not implemented yet" -ForegroundColor Yellow
}

Write-Host ""

# Test 6: Direct Homunculy execution (stateless)
Write-Host "6. Testing direct Homunculy execution (stateless)..." -ForegroundColor Yellow
$homunculyBody = @{
    user_id = "test-user-123"
    message = "Tell me a joke about programming"
    configuration = @{
        provider = "langraph"
        model = "gpt-4"
        temperature = 0.8
        system_message = "You are a funny programmer assistant."
        max_tokens = 500
    }
    context = @{}
} | ConvertTo-Json -Depth 3

try {
    $homunculyResponse = Invoke-RestMethod -Uri "$homunculyUrl/execute" -Method Post -Body $homunculyBody -ContentType "application/json"
    Write-Host "✓ Homunculy execution successful" -ForegroundColor Green
    Write-Host "  Response: $($homunculyResponse.message)" -ForegroundColor Gray
    Write-Host "  Provider Used: $($homunculyResponse.provider)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Database Architecture Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "MANAGEMENT SERVICE DATABASE (PostgreSQL - Port 5434):" -ForegroundColor Yellow
Write-Host "  • users - User accounts and subscription info" -ForegroundColor White
Write-Host "  • quotas - Usage limits and tracking" -ForegroundColor White
Write-Host "  • agent_assignments - Which agents users can access" -ForegroundColor White
Write-Host "  • usage_metrics - Billing/analytics data" -ForegroundColor White
Write-Host ""
Write-Host "HOMUNCULY SERVICE DATABASE (PostgreSQL - Port 5433):" -ForegroundColor Yellow
Write-Host "  • agents - Agent configurations (name, provider, model, prompts)" -ForegroundColor White
Write-Host "  • conversation_sessions - Multi-turn chat sessions" -ForegroundColor White
Write-Host "  • messages - Individual messages in conversations" -ForegroundColor White
Write-Host "  • emotional_states - User emotion tracking per session" -ForegroundColor White
Write-Host "  • context_data - Session-specific context/memory" -ForegroundColor White
Write-Host ""
Write-Host "DATA STORAGE STRATEGY:" -ForegroundColor Cyan
Write-Host "  Management Service (Business Logic):" -ForegroundColor White
Write-Host "    - User authentication & authorization" -ForegroundColor Gray
Write-Host "    - Quota enforcement & billing" -ForegroundColor Gray
Write-Host "    - Agent-to-user assignments" -ForegroundColor Gray
Write-Host "    - Usage analytics for billing" -ForegroundColor Gray
Write-Host ""
Write-Host "  Homunculy Service (Execution Engine):" -ForegroundColor White
Write-Host "    - Agent configurations & prompts" -ForegroundColor Gray
Write-Host "    - Conversation history & sessions" -ForegroundColor Gray
Write-Host "    - Emotional state tracking" -ForegroundColor Gray
Write-Host "    - Context/memory for multi-turn chats" -ForegroundColor Gray
Write-Host "    - Message metadata (timestamps, tokens)" -ForegroundColor Gray
Write-Host ""
