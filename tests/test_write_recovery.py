from types import SimpleNamespace

import pytest

from agent.orchestrator import AgentOrchestrator


class FakeMCPClient:

    def __init__(self):
        self.call_count = 0
        self.reconnect_count = 0

    async def list_tools(self):
        tool = SimpleNamespace(
            name="append_note",
            description="Append content to a note",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["filename", "content"]
            }
        )

        return SimpleNamespace(tools=[tool])

    async def call_tool(self, tool_name, arguments):
        self.call_count += 1

        # Simulate connection failure during execution
        raise ConnectionError("Connection closed")

    async def reconnect(self):
        self.reconnect_count += 1


class FakeLLM:

    def __init__(self):
        self.call_count = 0

    def generate_response(self, messages, tools=None):
        self.call_count += 1

        if self.call_count == 1:
            tool_call = SimpleNamespace(
                function=SimpleNamespace(
                    name="append_note",
                    arguments={
                        "filename": "recovery_write_test.txt",
                        "content": "INJECTED CONTENT"
                    }
                )
            )

            return SimpleNamespace(
                tool_calls=[tool_call],
                content=""
            )

        return SimpleNamespace(
            tool_calls=[],
            content="The append operation could not be confirmed."
        )


@pytest.mark.asyncio
async def test_write_operation_is_not_retried_after_connection_failure():

    mcp_client = FakeMCPClient()
    llm = FakeLLM()

    agent = AgentOrchestrator(
        llm=llm,
        mcp_client=mcp_client
    )

    messages = [
        {
            "role": "system",
            "content": "You are KAIRO."
        },
        {
            "role": "user",
            "content": "Append content to recovery_write_test.txt."
        }
    ]

    response = await agent.process_request(messages)

    # Verify write operation was attempted only once
    assert mcp_client.call_count == 1

    # Verify reconnection was attempted exactly once
    assert mcp_client.reconnect_count == 1

    # Verify the LLM generated its final response
    assert llm.call_count == 2

    assert response == "The append operation could not be confirmed."