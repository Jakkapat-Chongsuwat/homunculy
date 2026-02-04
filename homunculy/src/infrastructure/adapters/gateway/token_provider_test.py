"""Unit tests for ConfigTokenProvider."""

from infrastructure.adapters.gateway.token_provider import ConfigTokenProvider


def test_token_provider_reads_env(tmp_path, monkeypatch) -> None:
    config = tmp_path / "channels.json"
    config.write_text(
        """
        {"tenants": {"t1": {"channels": {"line": {"token_env": "LINE_TOKEN_T1", "secret_env": "LINE_SECRET_T1"}}}}}
        """,
        encoding="utf-8",
    )
    monkeypatch.setenv("LINE_TOKEN_T1", "token-1")
    monkeypatch.setenv("LINE_SECRET_T1", "secret-1")

    provider = ConfigTokenProvider(str(config))
    token = provider.get_token("t1", "line", "u1")
    secret = provider.get_secret("t1", "line", "u1")

    assert token == "token-1"
    assert secret == "secret-1"


def test_token_provider_missing_returns_none(tmp_path) -> None:
    config = tmp_path / "channels.json"
    config.write_text('{"tenants": {}}', encoding="utf-8")

    provider = ConfigTokenProvider(str(config))
    token = provider.get_token("t1", "line", "u1")

    assert token is None
