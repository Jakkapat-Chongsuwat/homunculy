from __future__ import annotations

import os
from argparse import ArgumentParser

from livekit.api import AccessToken, VideoGrants


def main() -> None:
    args = _parse_args()
    print(_token(args.room, args.identity, args.name, args.metadata))


def _parse_args():
    p = ArgumentParser(description="Generate a LiveKit room join token (JWT).")
    p.add_argument("--room", required=True)
    p.add_argument("--identity", default="dev-user")
    p.add_argument("--name", default="Dev User")
    p.add_argument("--metadata", default="")
    return p.parse_args()


def _token(room: str, identity: str, name: str, metadata: str) -> str:
    api_key, api_secret = _creds()
    grants = VideoGrants(
        room=room, room_join=True, can_publish=True, can_subscribe=True, can_publish_data=True
    )
    t = AccessToken(api_key, api_secret).with_identity(identity).with_name(name).with_grants(grants)
    return t.with_metadata(metadata).to_jwt() if metadata else t.to_jwt()


def _creds() -> tuple[str, str]:
    key = os.getenv("LIVEKIT_API_KEY", "devkey")
    secret = os.getenv("LIVEKIT_API_SECRET", "devsecret")
    return key, secret


if __name__ == "__main__":
    main()
