import asyncio

from ollama_client.client import KairoLLM
from client.mcp_client import MCPToolClient
from agent.tool_registry import ToolRegistry
from agent.tool_executor import ToolExecutor


async def main():

    mcp_client = MCPToolClient()
    registry = ToolRegistry()
    llm = KairoLLM()

    try:
        # 1. Connect to MCP server
        await mcp_client.connect()

        # 2. Discover and register tools
        response = await mcp_client.list_tools()
        ollama_tools = registry.register_tools(response.tools)

        # 3. Initialize tool executor
        executor = ToolExecutor(mcp_client, registry)

        # 4. Prepare user request
        messages = [
            {
                "role": "system",
                "content": llm.system_prompt
            },
            {
                "role": "user",
                "content": (
                    "Create a note named ideas.txt containing "
                    "three ideas for AI projects."
                )
            }
        ]

        # 5. Ask LLM to select a tool
        response = llm.generate_response(
            messages,
            tools=ollama_tools
        )

        # 6. Execute requested tools
        if response.tool_calls:

            for tool_call in response.tool_calls:

                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments

                print(f"\nRequested Tool: {tool_name}")
                print(f"Arguments: {arguments}")

                result = await executor.execute(
                    tool_name,
                    arguments
                )

                print("\n========== EXECUTION RESULT ==========")
                print(result.content)

        else:
            print("No tool calls generated.")
            print(response.content)

    except Exception as error:
        print(f"Error: {error}")

    finally:
        await mcp_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())