from types import SimpleNamespace

import pytest
import mcp.client.stdio as stdio_module

from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator


class CrashInjectingLLM:

    def __init__(self, captured_processes):
        self.captured_processes = captured_processes
        self.calls = []
        self.received_tool_result = None

    def generate_response(self, messages, tools=None):

        self.calls.append({
            "messages": messages.copy(),
            "tools": tools
        })

        # First response: request a read-only operation.
        if len(self.calls) == 1:

            # Kill the actual MCP server after tool discovery
            # but before the Orchestrator executes the tool.
            assert len(self.captured_processes) == 1

            self.captured_processes[0].kill()

            return SimpleNamespace(
                content="",
                tool_calls=[
                    SimpleNamespace(
                        function=SimpleNamespace(
                            name="list_notes",
                            arguments={}
                        )
                    )
                ]
            )

        # Second response: inspect the recovered tool result.
        self.received_tool_result = messages[-1]["content"]

        return SimpleNamespace(
            content="KAIRO recovered from the MCP server crash and completed the request.",
            tool_calls=[]
        )


@pytest.mark.asyncio
async def test_orchestrator_automatically_recovers_from_server_process_crash(
    monkeypatch
):

    # Capture actual MCP server subprocesses.
    original_create_process = (
        stdio_module._create_platform_compatible_process
    )

    captured_processes = []

    async def capture_process(*args, **kwargs):

        process = await original_create_process(*args, **kwargs)

        captured_processes.append(process)

        return process

    monkeypatch.setattr(
        stdio_module,
        "_create_platform_compatible_process",
        capture_process
    )

    mcp_client = MCPToolClient()

    try:

        # 1. Start the actual MCP server.
        await mcp_client.connect()

        assert len(captured_processes) == 1

        original_process = captured_processes[0]
        original_pid = original_process.pid

        # 2. Track actual MCP tool execution attempts.
        original_call_tool = mcp_client.call_tool

        tool_attempts = []

        async def tracked_call_tool(tool_name, arguments):

            tool_attempts.append(tool_name)

            return await original_call_tool(
                tool_name,
                arguments
            )

        monkeypatch.setattr(
            mcp_client,
            "call_tool",
            tracked_call_tool
        )

        # 3. Initialize the crash-injecting LLM.
        llm = CrashInjectingLLM(captured_processes)

        # 4. Initialize the real Orchestrator.
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
                "content": "List all my notes."
            }
        ]

        # 5. Process the request.
        # The LLM kills the actual server before tool execution.
        # The Orchestrator must recover automatically.
        response = await agent.process_request(messages)

        # 6. Verify the actual server process was terminated.
        assert original_process.returncode is not None

        # 7. Verify that automatic recovery spawned a new process.
        assert len(captured_processes) == 2

        recovered_process = captured_processes[1]

        assert recovered_process.pid != original_pid
        assert recovered_process.returncode is None

        # 8. Verify that the failed operation was retried.
        assert tool_attempts == [
            "list_notes",
            "list_notes"
        ]

        # 9. Verify that the LLM received a successful tool result.
        assert llm.received_tool_result is not None

        assert (
            "Tool execution failed"
            not in llm.received_tool_result
        )

        # 10. Verify the final response.
        assert response == (
            "KAIRO recovered from the MCP server crash "
            "and completed the request."
        )

        assert len(llm.calls) == 2

    finally:

        # Disconnect whichever server process is currently active.
        await mcp_client.disconnect()