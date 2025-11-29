#!/usr/bin/env python3
"""
Fast Interactive WebSocket Chat Client with Real-time Audio.

Supports interruption - sending new message stops current audio.

Usage:
    python chat_client.py
"""

import asyncio

from session import ChatApp


async def main() -> None:
    """Main entry point."""
    app = ChatApp()
    try:
        await app.run()
    except (KeyboardInterrupt, EOFError):
        print("\n\nGoodbye!")


if __name__ == "__main__":
    asyncio.run(main())
