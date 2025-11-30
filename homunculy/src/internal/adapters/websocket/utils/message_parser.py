"""
Message Parser - Parse and validate WebSocket messages.

Single Responsibility: Convert raw JSON to typed message objects.
"""

import json
from typing import Optional, Tuple, Union

from internal.adapters.websocket.models.messages import (
    MessageType,
    ChatStreamRequest,
)


class ParseError:
    """Represents a parse error with code and message."""
    
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message


def parse_json(raw: str) -> Tuple[Optional[dict], Optional[ParseError]]:
    """Parse raw JSON string to dictionary."""
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as e:
        return None, ParseError("INVALID_JSON", f"Invalid JSON: {str(e)}")


def get_message_type(data: dict) -> Optional[str]:
    """Extract message type from parsed data."""
    return data.get("type")


def is_ping(message_type: str) -> bool:
    """Check if message type is PING."""
    return message_type == MessageType.PING


def is_chat_request(message_type: str) -> bool:
    """Check if message type is CHAT_REQUEST."""
    return message_type == MessageType.CHAT_REQUEST


def parse_chat_request(data: dict) -> Tuple[Optional[ChatStreamRequest], Optional[ParseError]]:
    """Parse dictionary to ChatStreamRequest."""
    try:
        return ChatStreamRequest(**data), None
    except Exception as e:
        return None, ParseError("INVALID_REQUEST", f"Invalid request: {str(e)}")


def parse_message(raw: str) -> Tuple[Optional[Union[ChatStreamRequest, str]], Optional[ParseError]]:
    """
    Parse raw message to typed object.
    
    Returns:
        - (ChatStreamRequest, None) for chat requests
        - ("ping", None) for ping messages
        - (None, ParseError) for errors
    """
    data, error = parse_json(raw)
    if error or data is None:
        return None, error or ParseError("PARSE_ERROR", "Failed to parse message")
    
    message_type = get_message_type(data)
    if not message_type:
        return None, ParseError("MISSING_TYPE", "Message type is required")
    
    if is_ping(message_type):
        return "ping", None
    
    if is_chat_request(message_type):
        return parse_chat_request(data)
    
    return None, ParseError("INVALID_MESSAGE_TYPE", f"Unknown message type: {message_type}")
