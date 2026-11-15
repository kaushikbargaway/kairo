from types import SimpleNamespace

import pytest

from agent.tool_executor import ToolExecutor


class FakeMCPClient:

    def __init__(self):
        self.call_count = 0

    async def call_tool(self, tool_name, arguments):
        self.call_count += 1
        return "Note deleted successfully."


class FakeToolRegistry:

    def get_tool(self, tool_name):
        if tool_name != "delete_note":
            return None

        return SimpleNamespace(
            name="delete_note",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                },
                "required": ["filename"]
            }
        )


@pytest.mark.asyncio
async def test_deletion_without_approval_handler():

    client = FakeMCPClient()

    executor = ToolExecutor(
        mcp_client=client,
        tool_registry=FakeToolRegistry()
    )

    result = await executor.execute(
        "delete_note",
        {"filename": "test.txt"}
    )

    assert result == (
        "Deletion cancelled: approval handler is not configured."
    )
    assert client.call_count == 0


@pytest.mark.asyncio
async def test_deletion_rejected_by_user():

    client = FakeMCPClient()

    executor = ToolExecutor(
        mcp_client=client,
        tool_registry=FakeToolRegistry(),
        approval_callback=lambda tool, args: False
    )

    result = await executor.execute(
        "delete_note",
        {"filename": "test.txt"}
    )

    assert result == "Deletion cancelled by the user."
    assert client.call_count == 0


@pytest.mark.asyncio
async def test_deletion_approved_by_user():

    client = FakeMCPClient()

    executor = ToolExecutor(
        mcp_client=client,
        tool_registry=FakeToolRegistry(),
        approval_callback=lambda tool, args: True
    )

    result = await executor.execute(
        "delete_note",
        {"filename": "test.txt"}
    )

    assert result == "Note deleted successfully."
    assert client.call_count == 1