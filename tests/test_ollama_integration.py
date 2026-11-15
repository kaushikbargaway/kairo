import os
import uuid

import pytest

from ollama_client.client import KairoLLM
from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator
from conversation.manager import ConversationManager


@pytest.mark.asyncio
async def test_kairo_real_ollama_mcp_integration():

    # Run this test only when explicitly enabled.
    if os.getenv("KAIRO_RUN_OLLAMA_INTEGRATION") != "1":
        pytest.skip(
            "Set KAIRO_RUN_OLLAMA_INTEGRATION=1 to run this test."
        )

    filename = f"kairo_ollama_test_{uuid.uuid4().hex[:8]}.txt"
    note_content = f"KAIRO Ollama integration test {uuid.uuid4().hex}"

    mcp_client = MCPToolClient()
    llm = KairoLLM(model="qwen3:1.7b")

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

        # Ask the actual LLM to create and read a note.
        user_request = (
            f"Create a note named '{filename}' with exactly this content: "
            f"'{note_content}'. "
            f"Then use the read_note tool to read that same note. "
            f"Do not claim completion until you have read it."
        )

        response = await conversation.send_message(user_request)

        # Inspect the conversation history.
        history = conversation.get_history()

        tool_messages = [
            message
            for message in history
            if message["role"] == "tool"
        ]

        executed_tools = [
            message["tool_name"]
            for message in tool_messages
        ]

        # Verify that the LLM selected both required tools.
        assert "create_note" in executed_tools
        assert "read_note" in executed_tools

        # Verify that the note was actually created.
        create_results = [
            message["content"]
            for message in tool_messages
            if message["tool_name"] == "create_note"
        ]

        assert any(
            "successfully created" in result.lower()
            for result in create_results
        )

        # Verify that read_note returned the exact content.
        read_results = [
            message["content"]
            for message in tool_messages
            if message["tool_name"] == "read_note"
        ]

        assert any(
            note_content in result
            for result in read_results
        )

        # Verify that KAIRO generated a final response.
        assert isinstance(response, str)
        assert response.strip()

        print("\n========== OLLAMA INTEGRATION RESULTS ==========")
        print("Model: qwen3:1.7b")
        print("Executed tools:", executed_tools)
        print("Created note:", filename)
        print("Note content verified successfully.")
        print("Final response:", response)
        print("================================================")

    finally:
        # Clean up the temporary note.
        try:
            await mcp_client.call_tool(
                "delete_note",
                {"filename": filename}
            )
        finally:
            await mcp_client.disconnect()