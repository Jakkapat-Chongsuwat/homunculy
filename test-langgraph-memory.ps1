# Test LangGraph Agent with LangMem Memory
# Tests conversation memory persistence across multiple messages

param(
    [string]$AgentName = "LangGraphMemoryTest"
)

$baseUrl = "http://localhost:8000/api/v1"

Write-Host "`n=== Creating LangGraph Agent with Memory ===" -ForegroundColor Cyan

$createAgentBody = @{
    name = $AgentName
    configuration = @{
        provider = "langraph"
        model_name = "gpt-4"
        temperature = 0.7
        max_tokens = 1000
        system_prompt = "You are a helpful assistant with excellent memory. You remember details about users and can recall them later."
        personality = @{
            name = "Memory Expert"
            description = "An AI assistant with excellent conversation memory"
            traits = @{
                friendliness = 0.9
                helpfulness = 0.95
                memory = 0.99
            }
            mood = "attentive"
        }
    }
} | ConvertTo-Json -Depth 10

try {
    $createResponse = Invoke-RestMethod -Uri "$baseUrl/agents" -Method POST -Body $createAgentBody -ContentType "application/json"
    $agentId = $createResponse.id
    
    Write-Host "✅ Agent created successfully!" -ForegroundColor Green
    Write-Host "Agent ID: $agentId" -ForegroundColor Yellow
    
    # Generate a session ID for conversation continuity
    $sessionId = [guid]::NewGuid().ToString()
    Write-Host "Session ID: $sessionId" -ForegroundColor Yellow
    
    # Test 1: Introduce yourself
    Write-Host "`n=== Test 1: Introduction ===" -ForegroundColor Cyan
    $message1 = "Hi! My name is Alice and I'm a software engineer working on AI systems."
    Write-Host "User: $message1" -ForegroundColor White
    
    $chatBody1 = @{ 
        message = $message1
        context = @{ session_id = $sessionId }
    } | ConvertTo-Json
    $response1 = Invoke-RestMethod -Uri "$baseUrl/agents/$agentId/chat" -Method POST -Body $chatBody1 -ContentType "application/json"
    
    Write-Host "Assistant: $($response1.message)" -ForegroundColor Green
    Write-Host "Confidence: $($response1.confidence)" -ForegroundColor Yellow
    
    Start-Sleep -Seconds 1
    
    # Test 2: Ask about name (should remember)
    Write-Host "`n=== Test 2: Name Recall ===" -ForegroundColor Cyan
    $message2 = "What's my name?"
    Write-Host "User: $message2" -ForegroundColor White
    
    $chatBody2 = @{ 
        message = $message2
        context = @{ session_id = $sessionId }
    } | ConvertTo-Json
    $response2 = Invoke-RestMethod -Uri "$baseUrl/agents/$agentId/chat" -Method POST -Body $chatBody2 -ContentType "application/json"
    
    Write-Host "Assistant: $($response2.message)" -ForegroundColor Green
    
    if ($response2.message -like "*Alice*") {
        Write-Host "✅ MEMORY TEST PASSED - Agent remembered name!" -ForegroundColor Green
    } else {
        Write-Host "❌ MEMORY TEST FAILED - Agent forgot name!" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 1
    
    # Test 3: Ask about profession (should remember)
    Write-Host "`n=== Test 3: Profession Recall ===" -ForegroundColor Cyan
    $message3 = "What do I do for work?"
    Write-Host "User: $message3" -ForegroundColor White
    
    $chatBody3 = @{ 
        message = $message3
        context = @{ session_id = $sessionId }
    } | ConvertTo-Json
    $response3 = Invoke-RestMethod -Uri "$baseUrl/agents/$agentId/chat" -Method POST -Body $chatBody3 -ContentType "application/json"
    
    Write-Host "Assistant: $($response3.message)" -ForegroundColor Green
    
    if ($response3.message -like "*software engineer*" -or $response3.message -like "*AI systems*") {
        Write-Host "✅ MEMORY TEST PASSED - Agent remembered profession!" -ForegroundColor Green
    } else {
        Write-Host "❌ MEMORY TEST FAILED - Agent forgot profession!" -ForegroundColor Red
    }
    
    # Test 4: Follow-up conversation
    Write-Host "`n=== Test 4: Contextual Memory ===" -ForegroundColor Cyan
    $message4 = "I also love playing guitar in my free time."
    Write-Host "User: $message4" -ForegroundColor White
    
    $chatBody4 = @{ 
        message = $message4
        context = @{ session_id = $sessionId }
    } | ConvertTo-Json
    $response4 = Invoke-RestMethod -Uri "$baseUrl/agents/$agentId/chat" -Method POST -Body $chatBody4 -ContentType "application/json"
    
    Write-Host "Assistant: $($response4.message)" -ForegroundColor Green
    
    Start-Sleep -Seconds 1
    
    # Test 5: Recall hobby
    Write-Host "`n=== Test 5: Hobby Recall ===" -ForegroundColor Cyan
    $message5 = "What hobby did I just mention?"
    Write-Host "User: $message5" -ForegroundColor White
    
    $chatBody5 = @{ 
        message = $message5
        context = @{ session_id = $sessionId }
    } | ConvertTo-Json
    $response5 = Invoke-RestMethod -Uri "$baseUrl/agents/$agentId/chat" -Method POST -Body $chatBody5 -ContentType "application/json"
    
    Write-Host "Assistant: $($response5.message)" -ForegroundColor Green
    
    if ($response5.message -like "*guitar*") {
        Write-Host "✅ MEMORY TEST PASSED - Agent remembered hobby!" -ForegroundColor Green
    } else {
        Write-Host "❌ MEMORY TEST FAILED - Agent forgot hobby!" -ForegroundColor Red
    }
    
    Write-Host "`n=== Memory Test Summary ===" -ForegroundColor Cyan
    Write-Host "Agent ID: $agentId" -ForegroundColor Yellow
    Write-Host "Provider: LangGraph with LangMem" -ForegroundColor Yellow
    Write-Host "Total Messages: 5" -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
}

Write-Host ""
