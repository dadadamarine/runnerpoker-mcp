"""Deterministic HTTP boundary fixtures. Every unhandled request fails closed."""

import json
from copy import deepcopy
from pathlib import Path

import httpx
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from runnerpoker_mcp import client
from runnerpoker_mcp.server import mcp


class FixtureAPI:
    def __init__(self, data):
        self.data = deepcopy(data)
        self.requests = []
        self.overrides = {}

    def __call__(self, request):
        assert request.method == "GET"
        assert request.url.host == "api.runnerpoker.com"
        assert request.headers["Authorization"] == "Bearer fixture-token"
        assert request.headers["X-User-Seq"] == "42"
        self.requests.append(request)
        path = request.url.path
        if path in self.overrides:
            override = self.overrides[path]
            if isinstance(override, Exception):
                raise override
            if isinstance(override, httpx.Response):
                return override
            return httpx.Response(200, json=override)
        routes = {
            "/api/v1/craft/timeline": "timeline",
            "/api/v1/craft/timeline/2026-11-07": "timeline_day",
            "/api/v1/craft/holdem/sessions": "sessions",
            "/api/v1/craft/holdem/sessions/123456/performance": "performance",
            "/api/v1/craft/holdem/summary": "summary",
            "/api/v1/craft/hud": "hud",
            "/api/v1/craft/holdem/positions": "positions",
        }
        if path in routes:
            return httpx.Response(200, json=self.data[routes[path]])
        if path == "/hand-histories":
            cursor = request.url.params.get("Cursor")
            assert cursor in {None, "fixture-page-2"}
            return httpx.Response(200, json=self.data["hand_pages"][int(cursor is not None)])
        if path.startswith("/hand-histories/v2/"):
            hand_id = path.rsplit("/", 1)[-1]
            assert hand_id in self.data["hand_details"], "Unexpected hand ID"
            return httpx.Response(200, json=self.data["hand_details"][hand_id])
        raise AssertionError(f"Unhandled fixture route: {path}")


@pytest.fixture
def fixture_api(tmp_path, monkeypatch):
    data = json.loads((Path(__file__).parent / "fixtures/responses.json").read_text())
    api = FixtureAPI(data)
    auth = tmp_path / "credentials.json"
    auth.write_text(json.dumps({"accessToken": "fixture-token", "userSeq": 42}))
    auth.chmod(0o600)
    monkeypatch.setenv("RUNNERPOKER_AUTH_FILE", str(auth))
    original = httpx.AsyncClient
    monkeypatch.setattr(
        client.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(api), **kwargs),
    )
    return api


class MCPFixtureSession:
    async def call_tool(self, name, arguments):
        # Enter/exit AnyIO cancel scopes in the same task, including error cases.
        # pytest-asyncio runs async-yield fixture teardown in a separate task.
        async with create_connected_server_and_client_session(mcp) as session:
            return await session.call_tool(name, arguments)


@pytest.fixture
def mcp_session(fixture_api):
    return MCPFixtureSession()
