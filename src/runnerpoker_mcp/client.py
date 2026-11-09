"""Explicit GET-only API adapter; endpoint names come from Craft's public JS bundle."""

import re
from datetime import date, datetime, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

import httpx

from .auth import LOGIN_URL, Credentials, RunnerPokerError
from .session_refresh import refresh_credentials

BASE_URL = "https://api.runnerpoker.com"
Period = Literal["all", "today", "thisWeek", "thisMonth", "custom"]


def validate_date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise RunnerPokerError("Date must use YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise RunnerPokerError("Invalid calendar date.") from None


def timeline_params(
    period: Period, start_date: str | None, end_date: str | None, page: int, page_size: int
) -> dict[str, Any]:
    if period not in {"all", "today", "thisWeek", "thisMonth", "custom"}:
        raise RunnerPokerError("Unsupported period.")
    if (
        isinstance(page, bool)
        or not isinstance(page, int)
        or page < 1
        or isinstance(page_size, bool)
        or not isinstance(page_size, int)
        or not 1 <= page_size <= 100
    ):
        raise RunnerPokerError("page must be >= 1; page_size must be between 1 and 100.")
    if period != "custom" and (start_date is not None or end_date is not None):
        raise RunnerPokerError("Date arguments require period=custom.")
    params: dict[str, Any] = {"Period": period, "Page": page, "PageSize": page_size}
    if period == "thisWeek":
        # Craft implements this preset as a rolling seven-day custom range.
        today = datetime.now(ZoneInfo("Asia/Seoul")).date()
        params.update(Period="custom", From=str(today - timedelta(days=6)), To=str(today))
    if period == "custom":
        if start_date is None or end_date is None:
            raise RunnerPokerError("custom requires start_date and end_date.")
        if validate_date(start_date) > validate_date(end_date):
            raise RunnerPokerError("start_date must not be after end_date.")
        params.update(From=start_date, To=end_date)
    return params


AUTH_REJECTED_STATUSES = {401, 403}


async def _send(
    path: str, params: dict[str, Any] | None, credentials: Credentials
) -> httpx.Response:
    headers = {
        "Authorization": f"Bearer {credentials.access_token}",
        "X-User-Seq": str(credentials.user_seq),
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            return await client.get(BASE_URL + path, params=params, headers=headers)
    except httpx.RequestError:
        raise RunnerPokerError("RunnerPoker network request failed.") from None


async def _send_with_session_refresh(path: str, params: dict[str, Any] | None) -> httpx.Response:
    """On an auth rejection, re-acquire the session from the browser once and retry."""
    # Reload on every request so rotation needs no restart.
    response = await _send(path, params, Credentials.load())
    if response.status_code not in AUTH_REJECTED_STATUSES:
        return response

    async def session_is_accepted(candidate: Credentials) -> bool:
        probe = await _send(path, params, candidate)
        return probe.status_code not in AUTH_REJECTED_STATUSES

    try:
        refreshed = await refresh_credentials(session_is_accepted)
    except RunnerPokerError as error:
        raise RunnerPokerError(
            f"Session expired or access denied, and automatic refresh failed: {error} "
            f"Log in again at {LOGIN_URL}."
        ) from None
    return await _send(path, params, refreshed)


async def get_json(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await _send_with_session_refresh(path, params)
    if response.status_code in AUTH_REJECTED_STATUSES:
        raise RunnerPokerError(
            f"Session expired or access denied. Log in again at {LOGIN_URL} "
            "and update your session credentials."
        )
    if response.status_code == 429:
        raise RunnerPokerError("RunnerPoker rate limit reached. Retry later.")
    if response.status_code != 200:
        raise RunnerPokerError(f"RunnerPoker returned HTTP {response.status_code}.")
    try:
        result = response.json()
    except ValueError:
        raise RunnerPokerError("RunnerPoker returned invalid JSON.") from None
    if not isinstance(result, dict):
        raise RunnerPokerError("RunnerPoker returned an unexpected response shape.")
    code = result.get("code")
    if isinstance(code, (int, float)) and code >= 4000:
        raise RunnerPokerError("RunnerPoker rejected the request.")
    return result


async def timeline(
    period: Period = "today",
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    params = timeline_params(period, start_date, end_date, page, page_size)
    return await get_json("/api/v1/craft/timeline", params)


async def timeline_day(day: str) -> dict[str, Any]:
    validate_date(day)
    return await get_json(f"/api/v1/craft/timeline/{day}")
