import pytest

from agent.orchestrator import AgentOrchestrator


class FakeMCPClient:

    def __init__(self):
        self.reconnect_count = 0

    async def reconnect(self):
        self.reconnect_count += 1
        raise RuntimeError("Server unavailable")


@pytest.mark.asyncio
async def test_reconnection_failure():

    client = FakeMCPClient()

    agent = AgentOrchestrator(
        llm=None,
        mcp_client=client
    )

    async def failing_operation():
        raise ConnectionError("Connection closed")

    with pytest.raises(
        ConnectionError,
        match="MCP reconnection failed"
    ):
        await agent._run_with_recovery(failing_operation)


@pytest.mark.asyncio
async def test_non_connection_error_does_not_trigger_reconnection():

    client = FakeMCPClient()

    agent = AgentOrchestrator(
        llm=None,
        mcp_client=client
    )

    async def failing_operation():
        raise ValueError("Invalid operation")

    with pytest.raises(ValueError, match="Invalid operation"):
        await agent._run_with_recovery(failing_operation)

    assert client.reconnect_count == 0


@pytest.mark.asyncio
async def test_maximum_tool_iterations():

    class FakeLLM:

        def __init__(self):
            self.call_count = 0

        def generate_response(self, messages, tools=None):
            self.call_count += 1

            tool_call = type("ToolCall", (), {
                "function": type("Function", (), {
                    "name": "read_note",
                    "arguments": {"filename": "test.txt"}
                })()
            })()

            return type("Response", (), {
                "tool_calls": [tool_call],
                "content": ""
            })()

    class FakeMCPClient:

        async def list_tools(self):
            tool = type("Tool", (), {
                "name": "read_note",
                "description": "Read a note",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"}
                    },
                    "required": ["filename"]
                }
            })()

            return type("ToolResponse", (), {
                "tools": [tool]
            })()

        async def call_tool(self, tool_name, arguments):
            return "Test note content"

        async def reconnect(self):
            raise AssertionError("Unexpected reconnection")

    llm = FakeLLM()
    client = FakeMCPClient()

    agent = AgentOrchestrator(
        llm=llm,
        mcp_client=client,
        max_iterations=3
    )

    messages = [
        {"role": "system", "content": "You are KAIRO."},
        {"role": "user", "content": "Read test.txt."}
    ]

    response = await agent.process_request(messages)

    assert response == "Maximum tool execution iterations reached."
    assert llm.call_count == 3


@pytest.mark.asyncio
async def test_tool_execution_failure_is_handled():

    from types import SimpleNamespace

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

            return SimpleNamespace(
                content=[
                    SimpleNamespace(text="Note not found.")
                ],
                is_error=True
            )

        async def reconnect(self):
            self.reconnect_count += 1

    class FakeLLM:

        def __init__(self):
            self.call_count = 0
            self.received_tool_error = None

        def generate_response(self, messages, tools=None):
            self.call_count += 1

            if self.call_count == 1:
                tool_call = SimpleNamespace(
                    function=SimpleNamespace(
                        name="read_note",
                        arguments={"filename": "missing.txt"}
                    )
                )

                return SimpleNamespace(
                    tool_calls=[tool_call],
                    content=""
                )

            # Capture the error received from the orchestrator
            self.received_tool_error = messages[-1]["content"]

            return SimpleNamespace(
                tool_calls=[],
                content="The requested note could not be found."
            )

    client = FakeMCPClient()
    llm = FakeLLM()

    agent = AgentOrchestrator(
        llm=llm,
        mcp_client=client
    )

    messages = [
        {"role": "system", "content": "You are KAIRO."},
        {"role": "user", "content": "Read missing.txt."}
    ]

    response = await agent.process_request(messages)

    # Verify the MCP tool was called exactly once
    assert client.call_count == 1

    # Verify no unnecessary reconnection occurred
    assert client.reconnect_count == 0

    # Verify the LLM received the tool error
    assert llm.received_tool_error == (
        "Tool execution failed: Note not found."
    )

    # Verify the LLM generated a final response
    assert response == (
        "The requested note could not be found."
    )

    assert llm.call_count == 2


@pytest.mark.asyncio
async def test_operation_fails_even_after_reconnection():

    class FakeMCPClient:

        def __init__(self):
            self.reconnect_count = 0

        async def reconnect(self):
            self.reconnect_count += 1

    client = FakeMCPClient()

    agent = AgentOrchestrator(
        llm=None,
        mcp_client=client
    )

    operation_count = 0

    async def failing_operation():
        nonlocal operation_count
        operation_count += 1

        if operation_count == 1:
            raise ConnectionError("Connection closed")

        raise RuntimeError("Operation still failing")

    with pytest.raises(
        ConnectionError,
        match="MCP operation failed even after reconnection"
    ):
        await agent._run_with_recovery(failing_operation)

    assert operation_count == 2
    assert client.reconnect_count == 1


def test_nested_connection_exception_detection():

    error = RuntimeError("MCP operation failed")
    error.__cause__ = ConnectionError("Connection closed")
    assert AgentOrchestrator._is_connection_error(error) is True


def test_exception_group_connection_detection():

    errors = ExceptionGroup(
        "Multiple MCP errors",
        [
            ValueError("Invalid operation"),
            ConnectionError("Connection closed")
        ]
    )

    assert AgentOrchestrator._is_connection_error(errors) is True


def test_extract_result_with_non_text_content():

    from types import SimpleNamespace

    content_item = SimpleNamespace(value="binary-data")

    result = SimpleNamespace(
        content=[
            SimpleNamespace(text="First result"),
            content_item
        ]
    )

    extracted = AgentOrchestrator._extract_result(result)

    assert extracted == f"First result\n{content_item}"


def test_circular_exception_reference():

    error = RuntimeError("Some error")

    error.__cause__ = error

    assert AgentOrchestrator._is_connection_error(error) is False


def test_connection_error_in_exception_context():

    try:
        raise ConnectionError("Connection closed")
    except ConnectionError:
        try:
            raise RuntimeError("Operation failed")
        except RuntimeError as error:
            assert AgentOrchestrator._is_connection_error(error) is True