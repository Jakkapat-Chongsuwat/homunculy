"""LiveKit agent worker entrypoint."""

from common.logger import get_logger
from livekit.agents import JobContext, WorkerOptions, cli

from internal.adapters.livekit.pipecat.pipeline import run_pipeline

logger = get_logger(__name__)


def run() -> None:
    cli.run_app(worker_options())


def worker_options() -> WorkerOptions:
    return WorkerOptions(entrypoint_fnc=entrypoint)


async def entrypoint(ctx: JobContext) -> None:
    await connect(ctx)
    await run_pipeline(ctx)


async def connect(ctx: JobContext) -> None:
    logger.info("Connecting to room", room=ctx.room.name)
    await ctx.connect()


if __name__ == "__main__":
    run()
