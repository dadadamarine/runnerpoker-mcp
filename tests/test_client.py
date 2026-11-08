import json
import stat

import httpx
import pytest

from runnerpoker_mcp import client
from runnerpoker_mcp.auth import LOGIN_URL, Credentials, RunnerPokerError
from runnerpoker_mcp.auth import main as save_auth


@pytest.fixture
def credentials(tmp_path, monkeypatch):
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps({"accessToken": "test-token", "userSeq": 42}))
    monkeypatch.setenv("RUNNERPOKER_AUTH_FILE", str(path))
    return path


@pytest.fixture
def mock_http(monkeypatch):
    original = httpx.AsyncClient

    def install(handler):
        monkeypatch.setattr(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
        )

    return install


def test_custom_dates_and_exact_query_names():
    assert client.timeline_params("custom", "2026-11-01", "2026-11-07", 2, 10) == {
        "Period": "custom",
        "From": "2026-11-01",
        "To": "2026-11-07",
        "Page": 2,
        "PageSize": 10,
    }


@pytest.mark.parametrize(
    "arguments",
    [
        ("all", "2026-11-01", None, 1, 10),
        ("custom", None, None, 1, 10),
        ("custom", "2026-11-07", "2026-11-01", 1, 10),
        ("custom", "2026-02-30", "2026-11-01", 1, 10),
        ("today", None, None, 0, 10),
        ("today", None, None, 1, 101),
        ("today", None, None, True, 10),
        ("unknown", None, None, 1, 10),
    ],
)
def test_invalid_query_arguments(arguments):
    with pytest.raises(RunnerPokerError):
        client.timeline_params(*arguments)


def test_week_is_seven_day_custom_range():
    from datetime import date

    params = client.timeline_params("thisWeek", None, None, 1, 10)
    assert params["Period"] == "custom"
    assert (date.fromisoformat(params["To"]) - date.fromisoformat(params["From"])).days == 6


async def test_timeline_preserves_response_and_auth_headers(credentials, mock_http):
    payload = {"performance": {"profit": 123}, "days": {"items": [], "totalPages": 1}}

    def handler(request):
        assert request.method == "GET"
        assert request.url.host == "api.runnerpoker.com"
        assert request.url.path == "/api/v1/craft/timeline"
        assert request.url.params["Page"] == "2"
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["X-User-Seq"] == "42"
        return httpx.Response(200, json=payload)

    mock_http(handler)
    assert await client.timeline(page=2) == payload


async def test_day_path_and_credential_rotation(credentials, mock_http):
    mock_http(
        lambda request: httpx.Response(
            200,
            json={
                "items": [],
                "authorization_seen": request.headers["Authorization"],
                "path": request.url.path,
            },
        )
    )
    credentials.write_text(json.dumps({"accessToken": "rotated", "userSeq": 42}))
    result = await client.timeline_day("2026-11-07")
    assert result["authorization_seen"] == "Bearer rotated"
    assert result["path"] == "/api/v1/craft/timeline/2026-11-07"


@pytest.mark.parametrize("day", ["../account", "20261107", "2026-11-07?userSeq=99"])
async def test_day_rejects_path_injection(day):
    with pytest.raises(RunnerPokerError):
        await client.timeline_day(day)


@pytest.mark.parametrize("status", [302, 401, 403, 429, 500])
async def test_http_errors_never_echo_upstream_body(credentials, mock_http, status):
    mock_http(lambda request: httpx.Response(status, text="private upstream body test-token"))
    with pytest.raises(RunnerPokerError) as error:
        await client.timeline()
    assert "private" not in str(error.value)
    assert "test-token" not in str(error.value)


@pytest.mark.parametrize("payload", [[1], {"code": 4001, "message": "private"}])
async def test_invalid_or_rejected_response(credentials, mock_http, payload):
    mock_http(lambda request: httpx.Response(200, json=payload))
    with pytest.raises(RunnerPokerError):
        await client.timeline()


async def test_invalid_json(credentials, mock_http):
    mock_http(lambda request: httpx.Response(200, text="not json"))
    with pytest.raises(RunnerPokerError, match="invalid JSON"):
        await client.timeline()


async def test_array_query_uses_repeated_unbracketed_keys(credentials, mock_http):
    def handler(request):
        assert request.url.params.get_list("ChannelIds") == ["3", "4"]
        assert request.url.params.get_list("ParticipantIds") == ["12", "13"]
        assert "ChannelIds[]" not in request.url.params
        return httpx.Response(200, json={"items": []})

    mock_http(handler)
    await client.get_json("/api/v1/craft/hud", {"ChannelIds": [3, 4], "ParticipantIds": [12, 13]})


async def test_network_error_is_sanitized(credentials, mock_http):
    def handler(request):
        raise httpx.ConnectError("private secret", request=request)

    mock_http(handler)
    with pytest.raises(RunnerPokerError, match="network request failed"):
        await client.timeline()


def test_missing_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNNERPOKER_AUTH_FILE", str(tmp_path / "missing"))
    with pytest.raises(RunnerPokerError, match="Credentials unavailable"):
        Credentials.load()


@pytest.mark.parametrize(
    "data",
    [
        [],
        {},
        {"accessToken": "a\nb", "userSeq": 1},
        {"accessToken": "abc", "userSeq": True},
        {"accessToken": "abc", "userSeq": -1},
    ],
)
def test_invalid_credentials(data):
    with pytest.raises(RunnerPokerError):
        Credentials.parse(data)


def test_auth_save_is_private_and_does_not_print_token(tmp_path, monkeypatch, capsys):
    import io

    target = tmp_path / "auth" / "credentials.json"
    monkeypatch.setenv("RUNNERPOKER_AUTH_FILE", str(target))
    monkeypatch.setattr("sys.stdin", io.StringIO('{"accessToken":"secret","userSeq":42}'))
    save_auth()
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert Credentials.load().user_seq == 42
    captured = capsys.readouterr()
    assert not captured.out and "secret" not in captured.err


async def test_expired_session_error_includes_login_url(monkeypatch, tmp_path):
    auth = tmp_path / "credentials.json"
    auth.write_text(json.dumps({"accessToken": "abc.def", "userSeq": 1}))
    monkeypatch.setenv("RUNNERPOKER_AUTH_FILE", str(auth))

    real_client = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(lambda request: httpx.Response(401))
        return real_client(*args, **kwargs)

    monkeypatch.setattr(client.httpx, "AsyncClient", fake_client)
    with pytest.raises(RunnerPokerError, match="Session expired") as excinfo:
        await client.get_json("/api/v1/craft/timeline")
    assert LOGIN_URL in str(excinfo.value)
