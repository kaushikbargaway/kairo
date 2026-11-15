from types import SimpleNamespace
import uuid

import pytest

from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator
from conversation.manager import ConversationManager


class MockLLM:

    def __init__(self, responses):
        self.system_prompt = "You are KAIRO."
        self.responses = responses

    def generate_response(self, messages, tools=None):
        if not self.responses:
            raise RuntimeError("No scripted LLM responses remaining.")

        return self.responses.pop(0)


def make_tool_response(tool_name, arguments):
    return SimpleNamespace(
        content="",
        tool_calls=[
            SimpleNamespace(
                function=SimpleNamespace(
                    name=tool_name,
                    arguments=arguments
                )
            )
        ]
    )


def make_final_response(content):
    return SimpleNamespace(
        content=content,
        tool_calls=[]
    )


def extract_mcp_text(result):
    return "\n".join(
        item.text
        for item in result.content
        if hasattr(item, "text")
    )


async def create_conversation(mcp_client, llm, approval_callback=None):

    agent = AgentOrchestrator(
        llm=llm,
        mcp_client=mcp_client,
        approval_callback=approval_callback
    )

    conversation = ConversationManager(
        llm=llm,
        agent=agent
    )

    return conversation


# ---------------------------------------------------------
# TEST 1: Handle a nonexistent note
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_nonexistent_note_handling():

    filename = f"missing_{uuid.uuid4().hex[:8]}.txt"

    mcp_client = MCPToolClient()
    await mcp_client.connect()

    try:
        llm = MockLLM([
            make_tool_response(
                "read_note",
                {"filename": filename}
            ),
            make_final_response(
                "The requested note could not be found."
            )
        ])

        conversation = await create_conversation(
            mcp_client,
            llm
        )

        response = await conversation.send_message(
            f"Read the note named {filename}."
        )

        history = conversation.get_history()

        tool_messages = [
            message
            for message in history
            if message["role"] == "tool"
        ]

        assert len(tool_messages) == 1

        assert tool_messages[0]["tool_name"] == "read_note"

        assert filename in tool_messages[0]["content"]

        assert "Tool execution failed" not in tool_messages[0]["content"]

        assert response == (
            "The requested note could not be found."
        )

    finally:
        await mcp_client.disconnect()


# ---------------------------------------------------------
# TEST 2: Handle invalid tool arguments
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_tool_arguments_handling():

    mcp_client = MCPToolClient()
    await mcp_client.connect()

    try:
        llm = MockLLM([
            make_tool_response(
                "read_note",
                {}
            ),
            make_final_response(
                "The note request had invalid arguments."
            )
        ])

        conversation = await create_conversation(
            mcp_client,
            llm
        )

        response = await conversation.send_message(
            "Read a note."
        )

        history = conversation.get_history()

        tool_messages = [
            message
            for message in history
            if message["role"] == "tool"
        ]

        assert len(tool_messages) == 1

        assert tool_messages[0]["tool_name"] == "read_note"

        assert "Tool execution failed" in tool_messages[0]["content"]

        assert "Missing required arguments" in tool_messages[0]["content"]

        assert response == (
            "The note request had invalid arguments."
        )

    finally:
        await mcp_client.disconnect()


# ---------------------------------------------------------
# TEST 3: Prevent deletion without user approval
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_note_without_approval():

    filename = f"protected_{uuid.uuid4().hex[:8]}.txt"
    content = "This note must not be deleted without approval."

    mcp_client = MCPToolClient()
    await mcp_client.connect()

    try:
        # Create a real note directly through MCP.
        await mcp_client.call_tool(
            "create_note",
            {
                "filename": filename,
                "content": content
            }
        )

        llm = MockLLM([
            make_tool_response(
                "delete_note",
                {"filename": filename}
            ),
            make_final_response(
                "Deletion was cancelled because approval was not configured."
            )
        ])

        # No approval callback is provided.
        conversation = await create_conversation(
            mcp_client,
            llm
        )

        response = await conversation.send_message(
            f"Delete the note {filename}."
        )

        history = conversation.get_history()

        tool_messages = [
            message
            for message in history
            if message["role"] == "tool"
        ]

        assert len(tool_messages) == 1

        assert tool_messages[0]["tool_name"] == "delete_note"

        assert "Deletion cancelled" in tool_messages[0]["content"]

        # Verify the note still exists.
        result = await mcp_client.call_tool(
            "read_note",
            {"filename": filename}
        )

        assert content in extract_mcp_text(result)

        assert response == (
            "Deletion was cancelled because approval was not configured."
        )

    finally:
        # Explicitly clean up the protected test note.
        try:
            await mcp_client.call_tool(
                "delete_note",
                {"filename": filename}
            )
        finally:
            await mcp_client.disconnect()


# ---------------------------------------------------------
# TEST 4: Recover from MCP disconnection
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_connection_recovery():

    mcp_client = MCPToolClient()
    await mcp_client.connect()

    try:
        # Simulate an unexpected disconnection.
        await mcp_client.disconnect()

        llm = MockLLM([
            make_final_response(
                "KAIRO successfully recovered its MCP connection."
            )
        ])

        conversation = await create_conversation(
            mcp_client,
            llm
        )

        response = await conversation.send_message(
            "Hello KAIRO."
        )

        # The orchestrator should reconnect automatically
        # when its initial list_tools operation fails.
        assert mcp_client.client is not None

        assert mcp_client.client_context is not None

        assert response == (
            "KAIRO successfully recovered its MCP connection."
        )

    finally:
        await mcp_client.disconnect()