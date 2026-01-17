"""LiveKit agent worker entrypoint."""

from common.logger import get_logger
from livekit.agents import JobContext, WorkerOptions, cli

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
        await self._connect(ctx)
        await self._pipeline_runner(ctx)

    async def _connect(self, ctx: JobContext) -> None:
        """Connect to LiveKit room."""
        logger.info("Connecting to room", room=ctx.room.name)
        await ctx.connect()


def create_worker(pipeline_runner) -> LiveKitWorker:
    """Factory function to create LiveKit worker."""
    return LiveKitWorker(pipeline_runner)


# Standalone run support
def run_standalone(pipeline_runner) -> None:
    """Run worker as standalone process."""
    worker = create_worker(pipeline_runner)
    worker.run()
