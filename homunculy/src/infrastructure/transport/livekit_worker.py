"""LiveKit agent worker entrypoint - WebRTC connection handler."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from uuid import uuid4

from livekit.agents import JobContext, WorkerOptions, cli

from common.logger import configure_logging, get_logger
from infrastructure.transport.pipecat_transport import extract_livekit_parts

logger = get_logger(__name__)


class LiveKitWorker:
    """LiveKit agent worker wrapper."""

    def __init__(self, pipeline_runner) -> None:
        self._pipeline_runner = pipeline_runner

    def run(self) -> None:
        """Run the worker CLI."""
        cli.run_app(self._worker_options())

    def _worker_options(self) -> WorkerOptions:
        """Create worker options with entrypoint."""
        return WorkerOptions(entrypoint_fnc=self._entrypoint)

    async def _entrypoint(self, ctx: JobContext) -> None:
        """Worker entrypoint handler."""
        await self._pipeline_runner(ctx)


def create_worker(pipeline_runner) -> LiveKitWorker:
    """Factory function to create LiveKit worker."""
    return LiveKitWorker(pipeline_runner)


def run_standalone(pipeline_runner) -> None:
    """Run worker as standalone process."""
    worker = create_worker(pipeline_runner)
    worker.run()


def main() -> None:
    """CLI entrypoint for worker."""
    configure_logging()
    _ = _parse_args()
    run_standalone(run_isolated_session)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LiveKit worker")
    p.add_argument("cmd", nargs="?", default="dev")
    return p.parse_args()


async def run_isolated_session(ctx: JobContext) -> None:
    await _connect(ctx)
    url, token, room = extract_livekit_parts(ctx)
    await _spawn_session(url, token, room, _session_id(ctx))


async def _connect(ctx: JobContext) -> None:
    logger.info("Connecting to room", room=ctx.room.name)
    await ctx.connect()


def _session_id(ctx: JobContext) -> str:
    job = getattr(ctx, "job", None)
    job_id = getattr(job, "id", "")
    return job_id or _fallback_session(ctx)


def _fallback_session(ctx: JobContext) -> str:
    room = getattr(getattr(ctx, "room", None), "name", "session")
    return f"{room}-{uuid4().hex}"


async def _spawn_session(url: str, token: str, room: str, session_id: str) -> None:
    env = _env(url, token, room, session_id)
    args = _command(url, token, room, session_id)
    process = await asyncio.create_subprocess_exec(*args, env=env)
    await process.wait()


def _env(url: str, token: str, room: str, session_id: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "LIVEKIT_URL": url,
            "LIVEKIT_TOKEN": token,
            "LIVEKIT_ROOM": room,
            "HOMUNCULY_SESSION_ID": session_id,
        }
    )
    return env


def _command(url: str, token: str, room: str, session_id: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "infrastructure.transport.session_process",
        "--url",
        url,
        "--token",
        token,
        "--room",
        room,
        "--session-id",
        session_id,
    ]


if __name__ == "__main__":
    main()
