"""Unit tests for Pipecat transport - testing public API."""

from infrastructure.transport.pipecat_transport import (
    TransportConfig,
    extract_livekit_parts,
)


class TestTransportConfig:
    """Tests for TransportConfig dataclass."""

    def test_default_values(self) -> None:
        config = TransportConfig()
        assert config.audio_out is True
        assert config.audio_in is True
        assert config.camera_in is False
        assert config.vad_enabled is True
        assert config.vad_passthrough is True

    def test_custom_values(self) -> None:
        config = TransportConfig(
            audio_out=False,
            vad_enabled=False,
        )
        assert config.audio_out is False
        assert config.vad_enabled is False


class TestExtractLivekitParts:
    """Tests for extract_livekit_parts public API."""

    def test_extracts_all_parts(self) -> None:
        ctx = _MockContext(
            url="wss://lk.example.com",
            token="token123",
            room_name="my-room",
        )
        url, token, room = extract_livekit_parts(ctx)
        assert url == "wss://lk.example.com"
        assert token == "token123"
        assert room == "my-room"

    def test_returns_empty_for_missing_info(self) -> None:
        url, token, room = extract_livekit_parts(object())
        assert url == ""
        assert token == ""
        assert room == ""

    def test_partial_context(self) -> None:
        ctx = _MockContext(url="wss://test.com")
        url, token, room = extract_livekit_parts(ctx)
        assert url == "wss://test.com"
        assert token == ""
        assert room == ""


class _MockInfo:
    """Mock for ctx._info."""

    def __init__(self, url: str = "", token: str = "") -> None:
        self.url = url
        self.token = token


class _MockRoom:
    """Mock for ctx.room."""

    def __init__(self, name: str = "") -> None:
        self.name = name


class _MockContext:
    """Mock JobContext for testing."""

    def __init__(
        self,
        url: str = "",
        token: str = "",
        room_name: str = "",
    ) -> None:
        self._info = _MockInfo(url, token)
        self.room = _MockRoom(room_name)
