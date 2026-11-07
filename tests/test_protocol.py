import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_real_stdio_handshake_tools_and_calls(tmp_path):
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "runnerpoker_mcp.server"],
        env={"RUNNERPOKER_AUTH_FILE": str(tmp_path / "missing.json")},
    )
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            tools = {tool.name: tool for tool in result.tools}
            assert set(tools) == {
                "auth_status",
                "get_timeline",
                "get_timeline_day",
                "list_hand_histories",
                "get_hand_history",
                "search_review_hands",
            }
            assert all(tool.annotations.readOnlyHint for tool in tools.values())
            status = await session.call_tool("auth_status", {})
            assert not status.isError
            assert status.structuredContent["configured"] is False
            invalid = await session.call_tool("get_timeline_day", {"day": "../account"})
            assert invalid.isError
            missing = await session.call_tool("get_timeline", {})
            assert missing.isError
            assert "Credentials unavailable" in missing.content[0].text
            invalid_hand = await session.call_tool("get_hand_history", {"hand_id": -1})
            assert invalid_hand.isError
            search = tools["search_review_hands"].inputSchema
            assert "pocket_pairs_only" in search["properties"]
            assert "reached_river" in search["properties"]
