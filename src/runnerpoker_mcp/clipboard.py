"""Local clipboard write for exported hand-history text."""

import os
import subprocess
import sys
from typing import Any

PBCOPY_COMMAND = ["/usr/bin/pbcopy"]
COPY_TIMEOUT_SECONDS = 5
# pbcopy decodes stdin with the process locale; under a non-UTF-8 locale
# Korean nicknames reach the clipboard garbled.
UTF8_LOCALE = "en_US.UTF-8"


def copy_text(text: str) -> dict[str, Any]:
    """Copy text to the macOS clipboard.

    Returns {"copied": True}, or {"copied": False, "reason": ...} on other
    platforms and when pbcopy fails. Never raises: the caller still has the text.
    """
    if sys.platform != "darwin":
        return {"copied": False, "reason": "clipboard copy supports macOS only"}
    try:
        subprocess.run(
            PBCOPY_COMMAND,
            input=text.encode("utf-8"),
            env={**os.environ, "LC_ALL": UTF8_LOCALE},
            check=True,
            capture_output=True,
            timeout=COPY_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return {"copied": False, "reason": f"pbcopy failed: {type(error).__name__}"}
    return {"copied": True}
