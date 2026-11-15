import pytest
from types import SimpleNamespace

from agent.tool_executor import ToolExecutor


class FakeToolRegistry:

    def __init__(self):
        self.tool = SimpleNamespace(
            name="read_note",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                },
                "required": ["filename"]
            }
        )

    def get_tool(self, tool_name):
        if tool_name == "read_note":
            return self.tool
        return None


@pytest.fixture
def executor():
    return ToolExecutor(
        mcp_client=None,
        tool_registry=FakeToolRegistry()
    )


def test_missing_required_argument(executor):
    with pytest.raises(ValueError, match="Missing required arguments"):
        executor.validate_arguments(
            executor.tool_registry.get_tool("read_note"),
            {}
        )


def test_unexpected_argument(executor):
    with pytest.raises(ValueError, match="Unexpected arguments"):
        executor.validate_arguments(
            executor.tool_registry.get_tool("read_note"),
            {
                "filename": "test.txt",
                "extra": "unexpected"
            }
        )


def test_valid_arguments(executor):
    executor.validate_arguments(
        executor.tool_registry.get_tool("read_note"),
        {"filename": "test.txt"}
    )


@pytest.mark.asyncio
async def test_unknown_tool(executor):
    with pytest.raises(ValueError, match="Unknown tool"):
        await executor.execute("unknown_tool", {})


def test_non_dictionary_arguments(executor):

    with pytest.raises(
        ValueError,
        match="Tool arguments must be a dictionary"
    ):
        executor.validate_arguments(
            executor.tool_registry.get_tool("read_note"),
            ["test.txt"]
        )