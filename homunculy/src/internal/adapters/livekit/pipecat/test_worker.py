from unittest.mock import AsyncMock, patch

import pytest

import internal.adapters.livekit.pipecat.worker as worker


def test_worker_options_uses_entrypoint():
    options = worker.worker_options()
    assert options.entrypoint_fnc == worker.entrypoint


@pytest.mark.asyncio
async def test_connect_calls_ctx_connect():
    ctx = AsyncMock()
    await worker.connect(ctx)
    ctx.connect.assert_awaited_once()


def test_run_invokes_cli():
    with patch("internal.adapters.livekit.pipecat.worker.cli.run_app") as run_app:
        worker.run()
        run_app.assert_called_once()
