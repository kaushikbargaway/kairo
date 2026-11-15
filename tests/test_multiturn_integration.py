import os
import uuid

import pytest

from ollama_client.client import KairoLLM
from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator
from conversation.manager import ConversationManager


@pytest.mark.asyncio
async def test_kairo_multiturn_conversation():

    if os.getenv("KAIRO_RUN_OLLAMA_INTEGRATION") != "1":
        pytest.skip(
            "Set KAIRO_RUN_OLLAMA_INTEGRATION=1 to run this test."
        )

    filename = f"kairo_multiturn_{uuid.uuid4().hex[:8]}.txt"
    note_content = f"Multi-turn context test {uuid.uuid4().hex}"

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

        # TURN 1: Create a note.
        first_response = await conversation.send_message(
            f"Create a note named '{filename}' "
            f"containing exactly: '{note_content}'."
        )

        history_after_first_turn = conversation.get_history()

        first_turn_tools = [
            message["tool_name"]
            for message in history_after_first_turn
            if message["role"] == "tool"
        ]

        assert "create_note" in first_turn_tools

        # TURN 2: Refer to the previous conversation.
        second_response = await conversation.send_message(
            f"Earlier, I asked you to create a note named "
            f"'{filename}'. Please use the read_note tool to "
            f"retrieve that note again and tell me its exact content."
        )

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

        # Verify both turns executed the expected tools.
        assert "create_note" in executed_tools
        assert "read_note" in executed_tools

        # Verify that the second turn retrieved the exact content.
        read_results = [
            message["content"]
            for message in tool_messages
            if message["tool_name"] == "read_note"
        ]

        assert any(
            note_content in result
            for result in read_results
        )

        # Verify conversation context was preserved.
        user_messages = [
            message["content"]
            for message in history
            if message["role"] == "user"
        ]

        assert len(user_messages) == 2
        assert filename in user_messages[0]
        assert filename in user_messages[1]

        # Verify both assistant responses exist.
        assert first_response.strip()
        assert second_response.strip()

        print("\n========== MULTI-TURN RESULTS ==========")
        print("Model: qwen3:1.7b")
        print("Turn 1: Note creation successful")
        print("Turn 2: Previous context referenced")
        print("Executed tools:", executed_tools)
        print("Retrieved content:", note_content)
        print("Final response:", second_response)
        print("=======================================")

    finally:
        try:
            await mcp_client.call_tool(
                "delete_note",
                {"filename": filename}
            )
        finally:
            await mcp_client.disconnect()