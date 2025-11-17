# Homunculy Test Script
# Quick script to test agent creation and chat functionality

param(
    [string]$AgentName = "TestAgent",
    [string]$Message = "Hello! Tell me a joke about AI."
)

$baseUrl = "http://localhost:8000/api/v1"

Write-Host "`n=== Creating AI Agent ===" -ForegroundColor Cyan

$createAgentBody = @{
    name = $AgentName
    configuration = @{
        provider = "openai"
        model_name = "gpt-4"
        temperature = 0.7
        max_tokens = 1000
        system_prompt = "You are a helpful and friendly AI assistant."
        personality = @{
            name = "Friendly Assistant"
            description = "A helpful and cheerful AI assistant"
            traits = @{
                friendliness = 0.9
                helpfulness = 0.95
                creativity = 0.8
            }
            mood = "cheerful"
        }
    }
} | ConvertTo-Json -Depth 10

try {
    $createResponse = Invoke-RestMethod -Uri "$baseUrl/agents" -Method POST -Body $createAgentBody -ContentType "application/json"
    $agentId = $createResponse.id
    
    Write-Host "✅ Agent created successfully!" -ForegroundColor Green
    Write-Host "Agent ID: $agentId" -ForegroundColor Yellow
    
    Write-Host "`n=== Sending Message ===" -ForegroundColor Cyan
    Write-Host "Message: $Message" -ForegroundColor White
    
    $chatBody = @{
        message = $Message
    } | ConvertTo-Json
    
    $chatResponse = Invoke-RestMethod -Uri "$baseUrl/agents/$agentId/chat" -Method POST -Body $chatBody -ContentType "application/json"
    
    Write-Host "`n=== Agent Response ===" -ForegroundColor Cyan
    Write-Host "Message: $($chatResponse.message)" -ForegroundColor Green
    Write-Host "Confidence: $($chatResponse.confidence)" -ForegroundColor Yellow
    Write-Host "Reasoning: $($chatResponse.reasoning)" -ForegroundColor Gray
    
    Write-Host "`n=== Retrieving Agent Details ===" -ForegroundColor Cyan
    $agentDetails = Invoke-RestMethod -Uri "$baseUrl/agents/$agentId" -Method GET
    
    Write-Host "Name: $($agentDetails.name)" -ForegroundColor White
    Write-Host "Status: $($agentDetails.status)" -ForegroundColor Yellow
    Write-Host "Active: $($agentDetails.is_active)" -ForegroundColor Green
    Write-Host "Created: $($agentDetails.created_at)" -ForegroundColor Gray
    
    Write-Host "`n✅ All tests completed successfully!" -ForegroundColor Green
    Write-Host "`nAgent ID for future use: $agentId" -ForegroundColor Magenta
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "`nTo chat again with this agent, use:" -ForegroundColor Cyan
Write-Host '$chatBody = @{ message = "Your message here" } | ConvertTo-Json' -ForegroundColor White
Write-Host "Invoke-RestMethod -Uri `"$baseUrl/agents/$agentId/chat`" -Method POST -Body `$chatBody -ContentType `"application/json`"" -ForegroundColor White
