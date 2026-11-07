"""Read credentials locally; never expose them as MCP arguments or results."""

import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


class RunnerPokerError(Exception):
    """A safe error message that may be returned to the MCP client."""


def credential_path() -> Path:
    return Path(
        os.environ.get("RUNNERPOKER_AUTH_FILE", "~/.config/runnerpoker-mcp/credentials.json")
    ).expanduser()


@dataclass(frozen=True)
class Credentials:
    access_token: str = field(repr=False)
    user_seq: int

    @classmethod
    def parse(cls, data: object) -> "Credentials":
        if not isinstance(data, dict):
            raise RunnerPokerError("Credentials must be a JSON object.")
        token, seq = data.get("accessToken"), data.get("userSeq")
        if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9._~+/\-]+=*", token):
            raise RunnerPokerError("accessToken must be a valid Bearer token.")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
            raise RunnerPokerError("userSeq must be a positive integer.")
        return cls(token, seq)

    @classmethod
    def load(cls) -> "Credentials":
        try:
            data = json.loads(credential_path().read_text())
        except (OSError, ValueError):
            raise RunnerPokerError(
                "Credentials unavailable. Run runnerpoker-auth with your own session JSON on stdin."
            ) from None
        return cls.parse(data)


def main() -> None:
    """Accept {accessToken, userSeq} on stdin and atomically save a private file."""
    try:
        credentials = Credentials.parse(json.load(sys.stdin))
        target = credential_path()
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=target.parent, prefix=".credentials-")
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(
                    {"accessToken": credentials.access_token, "userSeq": credentials.user_seq},
                    stream,
                )
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
    except (ValueError, OSError, RunnerPokerError):
        print(
            "Could not save credentials: expected accessToken and positive integer userSeq.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    print("RunnerPoker credentials saved (mode 0600).", file=sys.stderr)
