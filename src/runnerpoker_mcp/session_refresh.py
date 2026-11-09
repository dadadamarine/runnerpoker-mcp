"""Re-acquire the Craft session from the user's own Chrome profile.

Chrome's localStorage for the Default profile is copied into a throw-away profile directory so
Chrome itself parses it; the token never leaves memory except for the private credentials file.
When nobody is logged in, the login page opens in the user's real Chrome and the copy is polled
until a valid login appears.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from .auth import LOGIN_URL, Credentials, RunnerPokerError, save_credentials

# A script-free page on the Craft origin: the SPA clears the token on load when the session
# cookie is absent from the scratch profile, while localStorage stays readable here.
STORAGE_READ_URL = "https://craft.runnerpoker.com/robots.txt"
LOGIN_TIMEOUT_SECONDS = 300
LOGIN_POLL_SECONDS = 4
LOCAL_STORAGE_DIRECTORY = "Local Storage"

CredentialCheck = Callable[[Credentials], Awaitable[bool]]

_refresh_lock = asyncio.Lock()

_READ_STORAGE_SCRIPT = """() => ({
    token: localStorage.getItem('accessToken'),
    authStorage: localStorage.getItem('auth-storage'),
})"""


def chrome_user_data_path() -> Path:
    return Path(
        os.environ.get(
            "RUNNERPOKER_CHROME_USER_DATA", "~/Library/Application Support/Google/Chrome"
        )
    ).expanduser()


def chrome_profile_name() -> str:
    return os.environ.get("RUNNERPOKER_CHROME_PROFILE", "Default")


def credentials_from_storage(raw: object) -> Credentials | None:
    """Build credentials from the localStorage snapshot, or None when not logged in."""
    if not isinstance(raw, dict):
        return None
    token, auth_storage = raw.get("token"), raw.get("authStorage")
    if not isinstance(token, str) or not isinstance(auth_storage, str):
        return None
    try:
        user_seq = json.loads(auth_storage)["state"]["user"]["userSeq"]
        if isinstance(user_seq, str) and user_seq.isdigit():
            user_seq = int(user_seq)  # Craft stores the id as a numeric string.
        return Credentials.parse({"accessToken": token.strip('"'), "userSeq": user_seq})
    except (ValueError, KeyError, TypeError, RunnerPokerError):
        return None


def _copy_chrome_local_storage(destination: Path) -> bool:
    source = chrome_user_data_path() / chrome_profile_name() / LOCAL_STORAGE_DIRECTORY
    if not source.is_dir():
        return False
    target = destination / chrome_profile_name() / LOCAL_STORAGE_DIRECTORY
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("LOCK"))
    return True


async def _read_credentials(page: Any) -> Credentials | None:
    try:
        return credentials_from_storage(await page.evaluate(_READ_STORAGE_SCRIPT))
    except Exception:  # Navigation may still be in flight.
        return None


async def _read_from_chrome_profile(playwright: Any) -> Credentials | None:
    scratch = Path(tempfile.mkdtemp(prefix="runnerpoker-session-"))
    try:
        if not _copy_chrome_local_storage(scratch):
            return None
        context = await playwright.chromium.launch_persistent_context(
            str(scratch), channel="chrome", headless=True, locale="ko-KR"
        )
        try:
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(STORAGE_READ_URL)
            return await _read_credentials(page)
        finally:
            await context.close()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _open_login_page_in_chrome() -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", "-a", "Google Chrome", LOGIN_URL], check=False)
    else:
        webbrowser.open(LOGIN_URL)


async def _accepted_login(playwright: Any, check: CredentialCheck) -> Credentials | None:
    credentials = await _read_from_chrome_profile(playwright)
    if credentials is not None and await check(credentials):
        return credentials
    return None


async def _wait_for_login(playwright: Any, check: CredentialCheck) -> Credentials | None:
    _open_login_page_in_chrome()
    waited = 0.0
    while waited < LOGIN_TIMEOUT_SECONDS:
        await asyncio.sleep(LOGIN_POLL_SECONDS)
        waited += LOGIN_POLL_SECONDS
        credentials = await _accepted_login(playwright, check)
        if credentials is not None:
            return credentials
    return None


async def refresh_credentials(check: CredentialCheck) -> Credentials:
    """Existing Chrome login first; open the login page in Chrome only when it is invalid."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RunnerPokerError(
            "playwright is not installed; cannot refresh the session automatically."
        ) from None

    async with _refresh_lock:
        try:
            async with async_playwright() as playwright:
                credentials = await _accepted_login(playwright, check)
                if credentials is None:
                    credentials = await _wait_for_login(playwright, check)
        except RunnerPokerError:
            raise
        except Exception:
            raise RunnerPokerError(
                "Automatic session refresh failed (is Google Chrome installed?)."
            ) from None
        if credentials is None:
            raise RunnerPokerError(
                f"Login was not completed in time. Log in at {LOGIN_URL} and retry."
            )
        save_credentials(credentials)
        return credentials
