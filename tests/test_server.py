"""Basic tests for giphy_mcp_server tool registration."""

import json

from giphy_mcp_server.server import mcp


def test_tools_registered():
    tools = mcp._tool_manager.list_tools()
    names = {t.name for t in tools}
    assert "search_gifs" in names
    assert "get_trending_gifs" in names
    assert "get_random_gif" in names
    assert "get_gif_by_id" in names
    assert "translate" in names


def test_tool_count():
    tools = mcp._tool_manager.list_tools()
    assert len(tools) == 5
