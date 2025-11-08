"""
WebSocket Controllers.

This module provides WebSocket endpoints for real-time communication.
Controllers are intentionally thin and delegate message processing
to application use-cases.
"""

from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from usecases.ai_agent_ws import process_ws_message, process_ws_stream

# Import waifu router
from controllers.websocket import waifu_router

router = APIRouter()

# Include waifu routes
router.include_router(waifu_router.router)


@router.websocket("/agents/{agent_id}/chat")
async def websocket_agent_chat(
    websocket: WebSocket,
    agent_id: str,
):
    """WebSocket endpoint for real-time AI agent chat."""
    await websocket.accept()

    try:
        await websocket.send_json({
            "type": "system",
            "message": f"Connected to AI Agent {agent_id}",
            "timestamp": "now",
        })

        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})
            thread_id = websocket.query_params.get("thread_id") or None

            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message cannot be empty",
                    "timestamp": "now",
                })
                continue

            try:
                response = await process_ws_message(
                    agent_id=agent_id,
                    message=message,
                    thread_id=thread_id,
                    context=context,
                )

                await websocket.send_json({
                    "type": "response",
                    "message": response.message,
                    "confidence": response.confidence,
                    "reasoning": response.reasoning,
                    "metadata": response.metadata,
                    "timestamp": "now",
                })

            except Exception as exc:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Chat failed: {str(exc)}",
                    "timestamp": "now",
                })

    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Connection error",
                "timestamp": "now",
            })
        except Exception:
            pass


@router.websocket("/agents/{agent_id}/stream")
async def websocket_agent_stream(
    websocket: WebSocket,
    agent_id: str,
):
    await websocket.accept()

    try:
        await websocket.send_json({
            "type": "system",
            "message": f"Connected to AI Agent {agent_id} (stream)",
            "timestamp": "now",
        })

        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})
            thread_id = websocket.query_params.get("thread_id") or None

            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message cannot be empty",
                    "timestamp": "now",
                })
                continue

            try:
                async for chunk in process_ws_stream(
                    agent_id=agent_id,
                    message=message,
                    thread_id=thread_id,
                    context=context,
                ):
                    await websocket.send_json({
                        "type": "stream",
                        "message": chunk.message,
                        "confidence": chunk.confidence,
                        "reasoning": chunk.reasoning,
                        "metadata": chunk.metadata,
                        "timestamp": "now",
                    })

                await websocket.send_json({
                    "type": "stream_end",
                    "message": "stream_complete",
                    "timestamp": "now",
                })

            except Exception as exc:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Streaming failed: {str(exc)}",
                    "timestamp": "now",
                })

    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Connection error",
                "timestamp": "now",
            })
        except Exception:
            pass


@router.get("/chat", response_class=HTMLResponse)
async def chat_interface():
    """Simple HTML interface for testing WebSocket chat."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Agent WebSocket Chat</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
            #messageInput { width: 70%; padding: 5px; }
            button { padding: 5px 10px; }
            .message { margin-bottom: 5px; }
            .user { color: blue; }
            .agent { color: green; }
            .system { color: gray; font-style: italic; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>AI Agent WebSocket Chat</h1>
        <div>
            <label>Agent ID: <input type="text" id="agentId" value="test-agent" /></label>
            <label>Thread ID: <input type="text" id="threadId" placeholder="optional" /></label>
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        <div id="messages"></div>
        <div>
            <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)" />
            <button onclick="sendMessage()">Send</button>
        </div>

        <script>
            let websocket = null;

            function connect() {
                const agentId = document.getElementById('agentId').value;
                const threadId = document.getElementById('threadId').value;
                let url = `ws://localhost:8000/ws/agents/${agentId}/chat`;
                if (threadId) {
                    url += `?thread_id=${threadId}`;
                }

                websocket = new WebSocket(url);

                websocket.onopen = function() {
                    addMessage('system', 'Connected to WebSocket');
                };

                websocket.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage(data.type, data.message);
                };

                websocket.onclose = function() {
                    addMessage('system', 'Disconnected from WebSocket');
                };

                websocket.onerror = function(error) {
                    addMessage('error', 'WebSocket error: ' + error);
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
                        context: {}
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
                messageDiv.textContent = `[${new Date().toLocaleTimeString()}] ${type.toUpperCase()}: ${message}`;
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)