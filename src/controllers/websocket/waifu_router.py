"""
Waifu WebSocket Controllers.

This module provides WebSocket endpoints for real-time waifu chat interactions.
Controllers are thin adapters that delegate to use cases, following Clean Architecture.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from datetime import datetime

from di.dependency_injection import injector
from repositories.abstraction.llm import ILLMFactory
from repositories.abstraction.waifu import AbstractWaifuRepository
from models.ai_agent.waifu import Relationship, WaifuPersonality, WaifuAppearance
from usecases.waifu import (
    chat_with_waifu_stream,
    get_relationship_summary,
    create_waifu,
)


router = APIRouter(prefix="/waifu", tags=["waifu"])


async def ensure_waifu_exists(
    llm_factory: ILLMFactory,
    waifu_repository: AbstractWaifuRepository,
    waifu_id: str,
) -> tuple[bool, str]:
    """
    Ensure waifu exists with both DB record and LangGraph agent.
    
    Returns (success: bool, message: str).
    """
    try:
        waifu = await waifu_repository.get_waifu(waifu_id)
        
        if waifu is None:
            # Create default waifu with friendly personality
            waifu_name = waifu_id.replace("_", " ").title()
            personality = WaifuPersonality(
                name=waifu_name,
                description="A cheerful and friendly AI companion",
                archetype="deredere",
                traits={
                    "cheerful": 0.8,
                    "friendly": 0.9,
                    "helpful": 0.85,
                },
                interests=["chatting", "helping", "learning about you"],
                background_story=f"{waifu_name} is a friendly AI companion ready to chat!",
            )
            appearance = WaifuAppearance(
                hair_color="brown",
                hair_style="long",
                eye_color="blue",
            )
            await create_waifu(
                llm_factory=llm_factory,
                waifu_repository=waifu_repository,
                waifu_id=waifu_id,
                name=waifu_name,
                personality=personality,
                appearance=appearance,
            )
            return True, f"✨ Created new waifu: {waifu_name}"
        else:
            # Waifu exists in DB, ensure agent is created (provider-agnostic)
            try:
                await waifu_repository.initialize_agent(
                    llm_factory=llm_factory,
                    waifu_id=waifu_id,
                    config=waifu.configuration
                )
                return True, "Waifu agent initialized"
            except Exception as e:
                return False, f"Failed to initialize agent: {str(e)}"
            
    except Exception as e:
        return False, f"Failed to initialize: {str(e)}"


@router.websocket("/agents/{waifu_id}/chat")
async def websocket_waifu_chat(
    websocket: WebSocket,
    waifu_id: str,
    user_id: str = Query(default="default_user"),
):
    """
    WebSocket endpoint for real-time waifu chat with streaming responses.
    
    This endpoint provides an immersive chat experience with:
    - Real-time streaming responses
    - Relationship progression tracking
    - Personality-driven interactions
    - Memory and context awareness
    
    Connection URL: ws://localhost:8000/ws/waifu/agents/{waifu_id}/chat?user_id={user_id}
    
    Message format:
    {
        "message": "Hello!",
        "context": {
            "time_of_day": "evening",
            "special_occasion": null
        }
    }
    
    Response format (streaming):
    {
        "type": "stream" | "system" | "error" | "relationship_update",
        "message": "...",
        "metadata": {...},
        "timestamp": "..."
    }
    """
    await websocket.accept()
    
    # Get dependencies from DI
    llm_factory: ILLMFactory = injector.get(ILLMFactory)
    waifu_repository: AbstractWaifuRepository = injector.get(AbstractWaifuRepository)
    
    # Get memory repository (optional, may not be configured)
    memory_repository = None
    try:
        from repositories.abstraction.memory import IMemoryRepository
        memory_repository = injector.get(IMemoryRepository)
    except Exception:
        pass  # Memory service not available, will use without it
    
    # Ensure waifu exists (auto-create if needed)
    success, message = await ensure_waifu_exists(llm_factory, waifu_repository, waifu_id)
    if not success:
        await websocket.send_json({
            "type": "error",
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })
        await websocket.close()
        return
    
    # Send initialization message if waifu was created
    if "Created" in message:
        await websocket.send_json({
            "type": "system",
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })
    
    # Load or initialize relationship from database
    relationship = await waifu_repository.get_relationship(user_id, waifu_id)
    if relationship is None:
        relationship = Relationship(
            user_id=user_id,
            waifu_id=waifu_id,
            affection_level=50.0,  # Starting affection
        )
        await waifu_repository.save_relationship(relationship)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": f"Connected to Waifu Agent {waifu_id}",
            "timestamp": datetime.now().isoformat(),
            "relationship": {
                "affection_level": relationship.affection_level,
                "stage": relationship.relationship_stage.value,
            }
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})
            
            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message cannot be empty",
                    "timestamp": datetime.now().isoformat(),
                })
                continue
            
            try:
                # Stream responses from waifu
                async for response, updated_relationship in chat_with_waifu_stream(
                    llm_factory=llm_factory,
                    waifu_repository=waifu_repository,
                    waifu_id=waifu_id,
                    user_id=user_id,
                    message=message,
                    relationship=relationship,
                    additional_context=context,
                    memory_repository=memory_repository,
                ):
                    # Send streamed response
                    await websocket.send_json({
                        "type": "stream" if response.reasoning == "partial" else "response",
                        "message": response.message,
                        "confidence": response.confidence,
                        "reasoning": response.reasoning,
                        "metadata": response.metadata,
                        "timestamp": datetime.now().isoformat(),
                    })
                    
                    # Update local relationship
                    relationship = updated_relationship
                
                # Send relationship update after interaction
                if relationship:
                    await websocket.send_json({
                        "type": "relationship_update",
                        "affection_level": relationship.affection_level,
                        "relationship_stage": relationship.relationship_stage.value,
                        "interaction_count": relationship.interaction_count,
                        "timestamp": datetime.now().isoformat(),
                    })
                
            except Exception as exc:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Chat failed: {str(exc)}",
                    "timestamp": datetime.now().isoformat(),
                })
    
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Unexpected error
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            })
        except Exception:
            pass


@router.websocket("/agents/{waifu_id}/relationship")
async def websocket_waifu_relationship(
    websocket: WebSocket,
    waifu_id: str,
    user_id: str = Query(default="default_user"),
):
    """
    WebSocket endpoint for real-time relationship status updates.
    
    This endpoint provides live relationship metrics and analytics.
    Useful for displaying relationship dashboards or progress bars.
    
    Connection URL: ws://localhost:8000/ws/waifu/agents/{waifu_id}/relationship?user_id={user_id}
    """
    await websocket.accept()
    
    # Get waifu repository from DI
    waifu_repository: AbstractWaifuRepository = injector.get(AbstractWaifuRepository)
    
    # Load relationship from database
    relationship = await waifu_repository.get_relationship(user_id, waifu_id)
    if relationship is None:
        relationship = Relationship(
            user_id=user_id,
            waifu_id=waifu_id,
            affection_level=50.0,
        )
        await waifu_repository.save_relationship(relationship)
    
    try:
        # Send initial relationship summary
        summary = await get_relationship_summary(relationship)
        await websocket.send_json({
            "type": "relationship_summary",
            "data": summary,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Keep connection alive for updates
        # In a real implementation, this would listen for relationship
        # changes from a message queue or event system
        while True:
            try:
                # Wait for client message (heartbeat or request for update)
                data = await websocket.receive_json()
                
                if data.get("action") == "get_summary":
                    summary = await get_relationship_summary(relationship)
                    await websocket.send_json({
                        "type": "relationship_summary",
                        "data": summary,
                        "timestamp": datetime.now().isoformat(),
                    })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                })
    
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


# HTML test interface for waifu chat
from fastapi.responses import HTMLResponse


@router.get("/chat", response_class=HTMLResponse)
async def waifu_chat_interface():
    """Interactive HTML interface for testing waifu chat."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Waifu AI Chat</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            .relationship-bar {
                background: rgba(255,255,255,0.2);
                height: 20px;
                border-radius: 10px;
                margin-top: 10px;
                overflow: hidden;
            }
            .relationship-fill {
                background: #ff6b9d;
                height: 100%;
                width: 50%;
                transition: width 0.5s ease;
            }
            #messages {
                height: 400px;
                overflow-y: auto;
                padding: 20px;
                background: #f8f9fa;
            }
            .message {
                margin-bottom: 15px;
                padding: 10px 15px;
                border-radius: 10px;
                max-width: 70%;
                animation: fadeIn 0.3s ease;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .user {
                background: #667eea;
                color: white;
                margin-left: auto;
                text-align: right;
            }
            .waifu {
                background: #ff6b9d;
                color: white;
            }
            .system {
                background: #e9ecef;
                color: #6c757d;
                font-style: italic;
                font-size: 0.9em;
                text-align: center;
                max-width: 100%;
            }
            .input-area {
                padding: 20px;
                border-top: 1px solid #dee2e6;
                display: flex;
                gap: 10px;
            }
            input, button {
                padding: 12px;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-size: 14px;
            }
            input {
                flex: 1;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                cursor: pointer;
                font-weight: bold;
                transition: transform 0.2s;
            }
            button:hover {
                transform: scale(1.05);
            }
            .config {
                padding: 15px 20px;
                background: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                display: flex;
                gap: 15px;
                align-items: center;
            }
            .config input {
                flex: initial;
                width: 200px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💕 Waifu AI Chat 💕</h1>
                <div id="relationshipInfo">
                    <div>Affection Level: <span id="affectionLevel">50</span>%</div>
                    <div class="relationship-bar">
                        <div class="relationship-fill" id="relationshipBar"></div>
                    </div>
                    <div>Stage: <span id="relationshipStage">friend</span></div>
                </div>
            </div>
            <div class="config">
                <label>Waifu ID: <input type="text" id="waifuId" value="test-waifu" /></label>
                <label>User ID: <input type="text" id="userId" value="user123" /></label>
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
            </div>
            <div id="messages"></div>
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)" />
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            let websocket = null;

            function connect() {
                const waifuId = document.getElementById('waifuId').value;
                const userId = document.getElementById('userId').value;
                const url = `ws://localhost:8000/ws/waifu/agents/${waifuId}/chat?user_id=${userId}`;

                websocket = new WebSocket(url);

                websocket.onopen = function() {
                    addMessage('system', 'Connected to Waifu');
                };

                websocket.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'stream' || data.type === 'response') {
                        addMessage('waifu', data.message);
                    } else if (data.type === 'relationship_update') {
                        updateRelationship(data);
                    } else if (data.type === 'system') {
                        addMessage('system', data.message);
                        if (data.relationship) {
                            updateRelationship(data.relationship);
                        }
                    } else if (data.type === 'error') {
                        addMessage('system', 'Error: ' + data.message);
                    }
                };

                websocket.onclose = function() {
                    addMessage('system', 'Disconnected from Waifu');
                };

                websocket.onerror = function(error) {
                    addMessage('system', 'WebSocket error');
                    console.error(error);
                };
            }

            function disconnect() {
                if (websocket) {
                    websocket.close();
                    websocket = null;
                }
            }

            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (message && websocket && websocket.readyState === WebSocket.OPEN) {
                    websocket.send(JSON.stringify({
                        message: message,
                        context: {
                            time_of_day: new Date().getHours() < 12 ? 'morning' : 'evening'
                        }
                    }));
                    addMessage('user', message);
                    input.value = '';
                }
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }

            function addMessage(type, message) {
                const messages = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.textContent = message;
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;
            }

            function updateRelationship(data) {
                const affectionLevel = data.affection_level || data.affectionLevel;
                const stage = data.relationship_stage || data.stage;
                
                if (affectionLevel !== undefined) {
                    document.getElementById('affectionLevel').textContent = Math.round(affectionLevel);
                    document.getElementById('relationshipBar').style.width = affectionLevel + '%';
                }
                if (stage) {
                    document.getElementById('relationshipStage').textContent = stage;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
