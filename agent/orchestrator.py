from agent.tool_registry import ToolRegistry
from agent.tool_executor import ToolExecutor


class AgentOrchestrator:

    def __init__(
        self,
        llm,
        mcp_client,
        max_iterations=5,
        approval_callback=None
    ):
        self.llm = llm
        self.mcp_client = mcp_client
        self.max_iterations = max_iterations

        self.tool_registry = ToolRegistry()

        self.tool_executor = ToolExecutor(
            mcp_client,
            self.tool_registry,
            approval_callback=approval_callback
        )

    async def _run_with_recovery(
        self,
        operation,
        *args,
        retry_on_reconnect=True
    ):

        try:
            return await operation(*args)

        except Exception as error:

            if not self._is_connection_error(error):
                raise

            print("\n[KAIRO] MCP connection lost.")
            print("[KAIRO] Attempting automatic recovery...")

            try:
                await self.mcp_client.reconnect()

            except Exception as reconnect_error:
                raise ConnectionError(
                    "MCP reconnection failed. Please try again later."
                ) from reconnect_error

            print("[KAIRO] MCP connection restored.")

            # Avoid retrying operations that might have modified data
            if not retry_on_reconnect:
                raise ConnectionError(
                    "MCP connection was restored, but the operation's "
                    "execution status is uncertain. It was not retried "
                    "to avoid duplicate changes."
                ) from error

            # Retry the original operation once
            try:
                return await operation(*args)

            except Exception as retry_error:
                raise ConnectionError(
                    "MCP operation failed even after reconnection."
                ) from retry_error


    @staticmethod
    def _is_connection_error(error):

        connection_messages = [
            "connection closed",
            "connection lost",
            "not connected",
            "broken pipe",
            "connection reset",
            "connection aborted",
            "transport is closed",
            "stream is closed"
        ]

        pending = [error]
        visited = set()

        while pending:

            current = pending.pop()

            if id(current) in visited:
                continue

            visited.add(id(current))

            message = str(current).lower()

            if any(text in message for text in connection_messages):
                return True

            if current.__cause__:
                pending.append(current.__cause__)

            if current.__context__:
                pending.append(current.__context__)

            # Inspect nested exceptions in ExceptionGroup
            pending.extend(getattr(current, "exceptions", ()))

        return False

    async def process_request(self, messages):

        # 1. Discover available MCP tools with recovery
        response = await self._run_with_recovery(
            self.mcp_client.list_tools
        )

        mcp_tools = response.tools

        # 2. Register and convert tools
        ollama_tools = self.tool_registry.register_tools(
            mcp_tools
        )

        # 3. Start the agent execution loop
        for iteration in range(self.max_iterations):

            # Ask LLM to process the request
            response = self.llm.generate_response(
                messages,
                tools=ollama_tools
            )

            # 4. Check whether the LLM requested a tool
            if not response.tool_calls:

                final_response = response.content or ""

                messages.append({
                    "role": "assistant",
                    "content": final_response
                })

                return final_response

            # 5. Preserve the assistant's tool-call message
            assistant_tool_calls = []

            for tool_call in response.tool_calls:

                assistant_tool_calls.append({
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })

            messages.append({
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": assistant_tool_calls
            })

            # 6. Execute requested tools
            for tool_call in response.tool_calls:

                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments

                print(f"\n[KAIRO] Executing tool: {tool_name}")

                try:
                    # Identify operations that are safe to retry
                    read_only_tools = {
                        "read_note",
                        "list_notes",
                        "search_notes"
                    }

                    result = await self._run_with_recovery(
                        self.tool_executor.execute,
                        tool_name,
                        arguments,
                        retry_on_reconnect=tool_name in read_only_tools
                    )

                    tool_result = self._extract_result(result)

                    # Check whether the MCP server reported an error
                    if getattr(result, "is_error", False):
                        raise RuntimeError(tool_result)

                except Exception as error:
                    tool_result = f"Tool execution failed: {error}"

                print(f"[KAIRO] Tool result: {tool_result}")

                # 7. Send execution result back to LLM
                messages.append({
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": tool_result
                })

        return "Maximum tool execution iterations reached."

    @staticmethod
    def _extract_result(result):

        if hasattr(result, "content"):

            contents = []

            for item in result.content:

                if hasattr(item, "text"):
                    contents.append(item.text)

                else:
                    contents.append(str(item))

            return "\n".join(contents)

        return str(result)