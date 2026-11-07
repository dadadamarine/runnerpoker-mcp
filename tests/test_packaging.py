"""Keep all supported hosts on the same published read-only server release."""

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(name):
    return json.loads((ROOT / name).read_text())


def test_hosts_share_identity_and_release_version():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    for path in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
        manifest = read_json(path)
        assert manifest["name"] == "runnerpoker"
        assert manifest["version"] == version


def test_both_marketplaces_resolve_the_plugin_inside_the_repository():
    claude = read_json(".claude-plugin/marketplace.json")
    codex = read_json(".agents/plugins/marketplace.json")
    assert claude["name"] == codex["name"] == "runnerpoker-community"
    assert claude["plugins"][0]["name"] == codex["plugins"][0]["name"] == "runnerpoker"
    assert claude["plugins"][0]["source"] == "./"
    assert codex["plugins"][0]["source"] == {"source": "local", "path": "./"}


def test_server_launch_is_pinned_and_contains_no_personal_paths_or_credentials():
    legacy = read_json(".mcp.json")["mcpServers"]["runnerpoker"]
    portable = read_json("mcp.json")["mcpServers"]["runnerpoker"]
    assert portable == {"type": "stdio", **legacy}
    assert legacy["command"] == "uvx"
    assert legacy["args"][:3] == ["--python", "3.11", "--from"]
    assert re.fullmatch(
        r"git\+https://github.com/dadadamarine/runnerpoker-mcp\.git@[0-9a-f]{40}",
        legacy["args"][3],
    )
    assert legacy["args"][4:] == ["runnerpoker-mcp"]
    assert "env" not in legacy
    assert read_json(".codex-plugin/plugin.json")["mcpServers"] == "./.mcp.json"
    assert read_json("plugin.json")["extensions"]["com.openai"]["requires_local_executor"]
