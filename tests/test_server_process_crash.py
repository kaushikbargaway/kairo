import pytest

import mcp.client.stdio as stdio_module

from client.mcp_client import MCPToolClient


@pytest.mark.asyncio
async def test_actual_mcp_server_process_crash_and_recovery(monkeypatch):
    """
    Verify recovery after the actual MCP server subprocess is killed.

    This test captures the real subprocess created by the MCP SDK,
    terminates it, reconnects the client, and verifies that a new
    server process starts successfully.
    """

    original_create_process = (
        stdio_module._create_platform_compatible_process
    )

    captured_processes = []

    async def capture_process(*args, **kwargs):
        process = await original_create_process(*args, **kwargs)
        captured_processes.append(process)
        return process

    monkeypatch.setattr(
        stdio_module,
        "_create_platform_compatible_process",
        capture_process,
    )

    mcp_client = MCPToolClient()

    try:
        # 1. Start the actual MCP server.
        await mcp_client.connect()

        assert len(captured_processes) == 1

        original_process = captured_processes[0]
        original_pid = original_process.pid

        assert original_process.returncode is None

        # 2. Kill the actual MCP server subprocess.
        original_process.kill()
        await original_process.wait()

        assert original_process.returncode is not None

        # 3. Reconnect the MCP client.
        await mcp_client.reconnect()

        # 4. Verify that a new server process was spawned.
        assert len(captured_processes) == 2

        recovered_process = captured_processes[1]

        assert recovered_process.pid != original_pid
        assert recovered_process.returncode is None

        # 5. Verify that the recovered server responds.
        tools_result = await mcp_client.list_tools()

        tool_names = [tool.name for tool in tools_result.tools]

        assert "create_note" in tool_names
        assert "read_note" in tool_names
        assert "list_notes" in tool_names
        assert "append_note" in tool_names
        assert "delete_note" in tool_names
        assert "search_notes" in tool_names

    finally:
        await mcp_client.disconnect()