from types import SimpleNamespace

import pytest

from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator
from conversation.manager import ConversationManager


class MockLLM:

    def __init__(self):
        self.system_prompt = "You are KAIRO."

        self.responses = [
            # First response: create a note
            SimpleNamespace(
                content="",
                tool_calls=[
                    SimpleNamespace(
                        function=SimpleNamespace(
                            name="create_note",
                            arguments={
                                "filename": "kairo_integration_test.txt",
                                "content": "KAIRO integration testing successful."
                            }
                        )
                    )
                ]
            ),

            # Second response: read the created note
            SimpleNamespace(
                content="",
                tool_calls=[
                    SimpleNamespace(
                        function=SimpleNamespace(
                            name="read_note",
                            arguments={
                                "filename": "kairo_integration_test.txt"
                            }
                        )
                    )
                ]
            ),

            # Third response: provide the final answer
            SimpleNamespace(
                content="The note was created and read successfully.",
                tool_calls=[]
            )
        ]

        self.calls = []

    def generate_response(self, messages, tools=None):
        self.calls.append({
            "messages": messages.copy(),
            "tools": tools
        })

        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_kairo_end_to_end_mcp_workflow():

    mcp_client = MCPToolClient()
    llm = MockLLM()

    await mcp_client.connect()

    try:
        agent = AgentOrchestrator(
            llm=llm,
            mcp_client=mcp_client
        )

        conversation = ConversationManager(
            llm=llm,
            agent=agent
        )

        # Send a request through the conversation manager
        response = await conversation.send_message(
            "Create a note and then read it."
        )

        # Verify final response
        assert response == (
            "The note was created and read successfully."
        )

        # Verify all three LLM interactions occurred
        assert len(llm.calls) == 3

        # Verify MCP tools were registered
        registered_tools = agent.tool_registry.tools

        assert "create_note" in registered_tools
        assert "read_note" in registered_tools

        # Verify the tool execution results in conversation history
        history = conversation.get_history()

        tool_messages = [
            message
            for message in history
            if message["role"] == "tool"
        ]

        assert len(tool_messages) == 2

        assert (
            "successfully created note"
            in tool_messages[0]["content"].lower()
        )

        assert (
            "KAIRO integration testing successful."
            in tool_messages[1]["content"]
        )

        # Verify the final assistant response is preserved
        assert history[-1]["role"] == "assistant"

        assert history[-1]["content"] == response

    finally:
        # Remove the test note
        try:
            await mcp_client.call_tool(
                "delete_note",
                {"filename": "kairo_integration_test.txt"}
            )
        finally:
            await mcp_client.disconnect()