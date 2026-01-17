"""Unit tests for LiveKit worker - testing public API."""

from unittest.mock import AsyncMock

from infrastructure.transport.livekit_worker import LiveKitWorker, create_worker


class TestLiveKitWorker:
    """Tests for LiveKitWorker public behavior."""

    def test_worker_accepts_pipeline_runner(self) -> None:
        runner = AsyncMock()
        worker = LiveKitWorker(runner)
        assert worker is not None

    def test_worker_has_run_method(self) -> None:
        runner = AsyncMock()
        worker = LiveKitWorker(runner)
        assert hasattr(worker, "run")
        assert callable(worker.run)


class TestCreateWorker:
    """Tests for create_worker factory function."""

    def test_returns_worker_instance(self) -> None:
        runner = AsyncMock()
        worker = create_worker(runner)
        assert isinstance(worker, LiveKitWorker)

    def test_factory_creates_runnable_worker(self) -> None:
        runner = AsyncMock()
        worker = create_worker(runner)
        assert hasattr(worker, "run")
