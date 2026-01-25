"""Unit tests for LiveKit token generation - testing public API."""

import time

import jwt

from infrastructure.transport.token import create_room_token


class TestCreateRoomToken:
    """Tests for create_room_token public API."""

    def test_creates_valid_jwt(self) -> None:
        token = create_room_token(
            api_key="key123",
            api_secret="secret123",
            room="test-room",
            identity="user-1",
        )
        assert isinstance(token, str)
        assert len(token) > 50

    def test_token_decodable_with_secret(self) -> None:
        token = create_room_token(
            api_key="key",
            api_secret="secret",
            room="room",
            identity="user",
        )
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        assert decoded["sub"] == "user"

    def test_token_contains_room_grants(self) -> None:
        token = create_room_token(
            api_key="key",
            api_secret="secret",
            room="my-room",
            identity="user",
        )
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        assert decoded["video"]["room"] == "my-room"
        assert decoded["video"]["roomJoin"] is True
        assert decoded["video"]["canPublish"] is True
        assert decoded["video"]["canSubscribe"] is True

    def test_token_has_correct_issuer(self) -> None:
        token = create_room_token(
            api_key="my_api_key",
            api_secret="secret",
            room="room",
            identity="user",
        )
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        assert decoded["iss"] == "my_api_key"

    def test_token_has_api_key_in_header(self) -> None:
        token = create_room_token(
            api_key="my_api_key",
            api_secret="secret",
            room="room",
            identity="user",
        )
        headers = jwt.get_unverified_header(token)
        assert headers["kid"] == "my_api_key"

    def test_custom_ttl(self) -> None:
        token = create_room_token(
            api_key="key",
            api_secret="secret",
            room="room",
            identity="user",
            ttl=7200,
        )
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        now = int(time.time())
        assert decoded["exp"] >= now + 7199

    def test_default_ttl_is_one_hour(self) -> None:
        token = create_room_token(
            api_key="key",
            api_secret="secret",
            room="room",
            identity="user",
        )
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        now = int(time.time())
        assert decoded["exp"] >= now + 3599
        assert decoded["exp"] <= now + 3601
