import asyncio
import json
import sys

import requests
import websockets


def create_agent():
    payload = {
        "provider": "pydantic_ai",
        "model_name": "gpt-4",
        "personality": {
            "name": "e2e-demo",
            "description": "E2E test agent",
            "traits": {},
            "mood": "neutral",
            "memory_context": "",
        },
        "system_prompt": "You are a helpful assistant for E2E testing.",
        "temperature": 0.7,
        "max_tokens": 2000,
        "tools": [],
    }

    resp = requests.post("http://localhost:8000/agents", json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("agent_id")


async def run_chat(agent_id: str):
    uri = f"ws://localhost:8000/ws/agents/{agent_id}/chat"
    print(f"Connecting to {uri}")
    async with websockets.connect(uri) as ws:
        # receive welcome
        welcome = await ws.recv()
        print("WELCOME:", welcome)

        message = {"message": "Hello from e2e test", "context": {}}
        await ws.send(json.dumps(message))

        # wait for a single response then exit
        resp = await ws.recv()
        print("RESPONSE:", resp)


def main():
    agent_id = create_agent()
    if not agent_id:
        print("Failed to create agent", file=sys.stderr)
        sys.exit(1)
    print("Created agent:", agent_id)

    asyncio.run(run_chat(agent_id))


if __name__ == "__main__":
    main()
