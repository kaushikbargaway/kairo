from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from client.mcp_client import MCPToolClient


@pytest.fixture
def mock_mcp():
    with patch("client.mcp_client.Client") as mock_client:
        yield mock_client


@pytest.fixture
def mcp_client():
    return MCPToolClient()


def test_initialization(mcp_client):
    assert mcp_client.client is None
    assert mcp_client.client_context is None

    assert mcp_client.server_params.args == [
        "-m",
        "servers.notepad.server"
    ]


def test_server_uses_current_python_interpreter(mcp_client):
    import sys

    assert mcp_client.server_params.command == sys.executable


@pytest.mark.asyncio
async def test_connect_successfully(mcp_client, mock_mcp):
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=MagicMock())

    mock_mcp.return_value = mock_context

    await mcp_client.connect()

    assert mcp_client.client is not None
    assert mcp_client.client_context is mock_context
    mock_context.__aenter__.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_failure(mcp_client, mock_mcp):
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(
        side_effect=RuntimeError("Server unavailable")
    )

    mock_mcp.return_value = mock_context

    with pytest.raises(
        ConnectionError,
        match="Failed to connect to KAIRO MCP Server"
    ):
        await mcp_client.connect()

    assert mcp_client.client is None
    assert mcp_client.client_context is None


@pytest.mark.asyncio
async def test_disconnect_successfully(mcp_client):
    mock_context = MagicMock()
    mock_context.__aexit__ = AsyncMock()

    mcp_client.client_context = mock_context
    mcp_client.client = MagicMock()

    await mcp_client.disconnect()

    assert mcp_client.client is None
    assert mcp_client.client_context is None
    mock_context.__aexit__.assert_awaited_once_with(None, None, None)


@pytest.mark.asyncio
async def test_disconnect_when_already_disconnected(mcp_client):
    await mcp_client.disconnect()

    assert mcp_client.client is None
    assert mcp_client.client_context is None


@pytest.mark.asyncio
async def test_list_tools_successfully(mcp_client):
    expected_tools = [MagicMock(), MagicMock()]

    mock_client = MagicMock()
    mock_client.list_tools = AsyncMock(return_value=expected_tools)

    mcp_client.client = mock_client

    result = await mcp_client.list_tools()

    assert result == expected_tools
    mock_client.list_tools.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_tools_when_disconnected(mcp_client):
    with pytest.raises(
        RuntimeError,
        match="MCP client is not connected"
    ):
        await mcp_client.list_tools()


@pytest.mark.asyncio
async def test_call_tool_successfully(mcp_client):
    expected_result = MagicMock()

    mock_client = MagicMock()
    mock_client.call_tool = AsyncMock(return_value=expected_result)

    mcp_client.client = mock_client

    result = await mcp_client.call_tool(
        "create_note",
        {"filename": "test.txt", "content": "Hello"}
    )

    assert result == expected_result

    mock_client.call_tool.assert_awaited_once_with(
        "create_note",
        {"filename": "test.txt", "content": "Hello"}
    )


@pytest.mark.asyncio
async def test_call_tool_when_disconnected(mcp_client):
    with pytest.raises(
        RuntimeError,
        match="MCP client is not connected"
    ):
        await mcp_client.call_tool("create_note", {})


@pytest.mark.asyncio
async def test_reconnect_successfully(mcp_client, mock_mcp):
    # Simulate an existing connection
    old_context = MagicMock()
    old_context.__aexit__ = AsyncMock()

    mcp_client.client_context = old_context
    mcp_client.client = MagicMock()

    # Simulate a fresh connection
    new_client = MagicMock()
    new_context = MagicMock()
    new_context.__aenter__ = AsyncMock(return_value=new_client)

    mock_mcp.return_value = new_context

    await mcp_client.reconnect()

    old_context.__aexit__.assert_awaited_once_with(None, None, None)

    assert mcp_client.client_context is new_context
    assert mcp_client.client is new_client


@pytest.mark.asyncio
async def test_reconnect_when_initially_disconnected(mcp_client, mock_mcp):
    new_client = MagicMock()
    new_context = MagicMock()
    new_context.__aenter__ = AsyncMock(return_value=new_client)

    mock_mcp.return_value = new_context

    await mcp_client.reconnect()

    assert mcp_client.client is new_client
    assert mcp_client.client_context is new_context


@pytest.mark.asyncio
async def test_reconnect_after_cleanup_failure(mcp_client, mock_mcp):
    old_context = MagicMock()
    old_context.__aexit__ = AsyncMock(
        side_effect=RuntimeError("Cleanup failed")
    )

    mcp_client.client_context = old_context
    mcp_client.client = MagicMock()

    new_client = MagicMock()
    new_context = MagicMock()
    new_context.__aenter__ = AsyncMock(return_value=new_client)

    mock_mcp.return_value = new_context

    await mcp_client.reconnect()

    assert mcp_client.client is new_client
    assert mcp_client.client_context is new_context


@pytest.mark.asyncio
async def test_reconnect_failure(mcp_client, mock_mcp):
    new_context = MagicMock()
    new_context.__aenter__ = AsyncMock(
        side_effect=RuntimeError("Server unavailable")
    )

    mock_mcp.return_value = new_context

    with pytest.raises(
        ConnectionError,
        match="Failed to connect to KAIRO MCP Server"
    ):
        await mcp_client.reconnect()

    assert mcp_client.client is None
    assert mcp_client.client_context is None