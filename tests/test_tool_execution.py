from types import SimpleNamespace

import pytest

from agent.orchestrator import AgentOrchestrator


class FakeMCPClient:

    def __init__(self):
        self.call_count = 0
        self.reconnect_count = 0

    async def list_tools(self):
        tool = SimpleNamespace(
            name="read_note",
            description="Read a note",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                },
                "required": ["filename"]
            }
        )

        return SimpleNamespace(tools=[tool])

    async def call_tool(self, tool_name, arguments):
        self.call_count += 1

        assert tool_name == "read_note"
        assert arguments == {"filename": "test.txt"}

        return SimpleNamespace(
            content=[
                SimpleNamespace(text="This is a test note.")
            ],
            is_error=False
        )

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
                    name="read_note",
                    arguments={"filename": "test.txt"}
                )
            )

            return SimpleNamespace(
                tool_calls=[tool_call],
                content=""
            )

        return SimpleNamespace(
            tool_calls=[],
            content="The note contains: This is a test note."
        )


@pytest.mark.asyncio
async def test_successful_tool_execution():

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
            "content": "Read test.txt."
        }
    ]

    response = await agent.process_request(messages)

    assert mcp_client.call_count == 1
    assert mcp_client.reconnect_count == 0
    assert llm.call_count == 2

    assert response == (
        "The note contains: This is a test note."
    )