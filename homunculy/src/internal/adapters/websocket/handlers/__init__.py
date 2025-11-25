"""
WebSocket Handlers.

Contains WebSocket endpoint handlers that receive requests
and delegate to appropriate managers/services.
"""

from .chat_handler import router as websocket_router

__all__ = ["websocket_router"]
