import asyncio
from types import SimpleNamespace

import pytest

from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator
from conversation.manager import ConversationManager


class MockLLM:

    def __init__(self):
        self.system_prompt = "You are KAIRO."
        self.calls = 0

    def generate_response(self, messages, tools=None):
        self.calls += 1

        return SimpleNamespace(
            content="KAIRO recovered successfully after the MCP server disconnected.",
            tool_calls=[]
        )


@pytest.mark.asyncio
async def test_mcp_server_crash_and_recovery():

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

        # Verify initial connection.
        assert mcp_client.client is not None

        # Simulate an unexpected connection loss.
        await mcp_client.disconnect()

        assert mcp_client.client is None

        # Send a request. The orchestrator should detect
        # the disconnection and attempt automatic recovery.
        response = await conversation.send_message(
            "Hello KAIRO. Are you operational?"
        )

        # Verify automatic reconnection.
        assert mcp_client.client is not None
        assert mcp_client.client_context is not None

        # Verify that the LLM received the request.
        assert llm.calls == 1

        # Verify the final response.
        assert response == (
            "KAIRO recovered successfully after the MCP server disconnected."
        )

        print("\n========== SERVER RECOVERY RESULTS ==========")
        print("Initial MCP connection: Successful")
        print("Simulated disconnection: Successful")
        print("Automatic reconnection: Successful")
        print("LLM request processing: Successful")
        print("Final response:", response)
        print("=============================================")

    finally:
        if mcp_client.client_context is not None:
            await mcp_client.disconnect()