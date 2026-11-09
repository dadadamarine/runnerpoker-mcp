import json
from contextlib import asynccontextmanager

import httpx
import pytest

from runnerpoker_mcp import client, session_refresh
from runnerpoker_mcp.auth import Credentials, RunnerPokerError

STALE = Credentials("stale.token", 1)
FRESH = Credentials("fresh.token", 1)


def storage_snapshot(token="abc.def", user_seq=7):
    return {
        "token": token,
        "authStorage": json.dumps({"state": {"user": {"userSeq": user_seq}}}),
    }


def test_credentials_from_storage_reads_token_and_user_seq():
    credentials = session_refresh.credentials_from_storage(storage_snapshot())
    assert credentials == Credentials("abc.def", 7)


def test_credentials_from_storage_strips_json_quotes_around_token():
    credentials = session_refresh.credentials_from_storage(storage_snapshot(token='"abc.def"'))
    assert credentials.access_token == "abc.def"


def test_credentials_from_storage_accepts_numeric_string_user_seq():
    credentials = session_refresh.credentials_from_storage(storage_snapshot(user_seq="42"))
    assert credentials == Credentials("abc.def", 42)


@pytest.mark.parametrize(
    "raw",
    [None, {}, {"token": None, "authStorage": None}, storage_snapshot(user_seq=0), "text"],
)
def test_credentials_from_storage_returns_none_when_logged_out(raw):
    assert session_refresh.credentials_from_storage(raw) is None


@pytest.fixture
def fake_playwright(monkeypatch):
    import playwright.async_api

    @asynccontextmanager
    async def fake_async_playwright():
        yield object()

    monkeypatch.setattr(playwright.async_api, "async_playwright", fake_async_playwright)


@pytest.fixture
def saved(monkeypatch):
    stored = []
    monkeypatch.setattr(session_refresh, "save_credentials", stored.append)
    return stored


async def always_accepted(credentials):
    return True


async def test_refresh_uses_existing_chrome_login_without_opening_login_page(
    fake_playwright, saved, monkeypatch
):
    async def from_saved(playwright, check):
        return FRESH

    async def from_window(playwright, check):
        raise AssertionError("login page must stay closed when the Chrome login works")

    monkeypatch.setattr(session_refresh, "_accepted_login", from_saved)
    monkeypatch.setattr(session_refresh, "_wait_for_login", from_window)
    assert await session_refresh.refresh_credentials(always_accepted) == FRESH
    assert saved == [FRESH]


async def test_refresh_opens_login_page_when_chrome_login_is_invalid(
    fake_playwright, saved, monkeypatch
):
    async def from_saved(playwright, check):
        return None

    async def from_window(playwright, check):
        return FRESH

    monkeypatch.setattr(session_refresh, "_accepted_login", from_saved)
    monkeypatch.setattr(session_refresh, "_wait_for_login", from_window)
    assert await session_refresh.refresh_credentials(always_accepted) == FRESH
    assert saved == [FRESH]


async def test_refresh_reports_timeout_when_login_never_completes(
    fake_playwright, saved, monkeypatch
):
    async def nothing(playwright, check):
        return None

    monkeypatch.setattr(session_refresh, "_accepted_login", nothing)
    monkeypatch.setattr(session_refresh, "_wait_for_login", nothing)
    with pytest.raises(RunnerPokerError, match="not completed"):
        await session_refresh.refresh_credentials(always_accepted)
    assert saved == []


@pytest.fixture
def stale_credentials_file(monkeypatch, tmp_path):
    auth = tmp_path / "credentials.json"
    auth.write_text(json.dumps({"accessToken": STALE.access_token, "userSeq": STALE.user_seq}))
    monkeypatch.setenv("RUNNERPOKER_AUTH_FILE", str(auth))


@pytest.fixture
def token_gated_api(monkeypatch):
    seen_tokens = []

    def handler(request):
        token = request.headers["Authorization"].removeprefix("Bearer ")
        seen_tokens.append(token)
        if token == FRESH.access_token:
            return httpx.Response(200, json={"code": 0, "data": []})
        return httpx.Response(401)

    real_client = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(client.httpx, "AsyncClient", fake_client)
    return seen_tokens


async def test_auth_rejection_refreshes_session_and_retries_once(
    stale_credentials_file, token_gated_api, monkeypatch
):
    async def refreshed(check):
        assert await check(FRESH)
        assert not await check(STALE)
        return FRESH

    monkeypatch.setattr(client, "refresh_credentials", refreshed)
    result = await client.get_json("/api/v1/craft/timeline")
    assert result["code"] == 0
    assert token_gated_api[:1] == [STALE.access_token]
    assert token_gated_api[-1] == FRESH.access_token


async def test_failed_refresh_surfaces_login_url(
    stale_credentials_file, token_gated_api, monkeypatch
):
    async def refused(check):
        raise RunnerPokerError("Login was not completed in time.")

    monkeypatch.setattr(client, "refresh_credentials", refused)
    with pytest.raises(RunnerPokerError, match="refresh failed") as error:
        await client.get_json("/api/v1/craft/timeline")
    assert client.LOGIN_URL in str(error.value)


def test_copy_chrome_local_storage_copies_data_and_skips_lock(monkeypatch, tmp_path):
    chrome = tmp_path / "chrome"
    storage = chrome / "Default" / "Local Storage" / "leveldb"
    storage.mkdir(parents=True)
    (storage / "000003.log").write_text("data")
    (storage / "LOCK").write_text("")
    monkeypatch.setenv("RUNNERPOKER_CHROME_USER_DATA", str(chrome))

    scratch = tmp_path / "scratch"
    assert session_refresh._copy_chrome_local_storage(scratch) is True
    copied = scratch / "Default" / "Local Storage" / "leveldb"
    assert (copied / "000003.log").read_text() == "data"
    assert not (copied / "LOCK").exists()


def test_copy_chrome_local_storage_returns_false_without_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("RUNNERPOKER_CHROME_USER_DATA", str(tmp_path / "missing"))
    assert session_refresh._copy_chrome_local_storage(tmp_path / "scratch") is False
