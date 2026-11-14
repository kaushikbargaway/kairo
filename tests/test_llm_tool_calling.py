import asyncio

from ollama_client.client import KairoLLM
from client.mcp_client import MCPToolClient
from agent.tool_registry import ToolRegistry


async def main():

    mcp_client = MCPToolClient()
    registry = ToolRegistry()
    llm = KairoLLM()

    try:
        # 1. Connect to MCP server
        await mcp_client.connect()

        # 2. Discover MCP tools
        response = await mcp_client.list_tools()
        mcp_tools = response.tools

        # 3. Convert MCP tools into Ollama format
        ollama_tools = registry.register_tools(mcp_tools)

        print(f"\nDiscovered {len(ollama_tools)} tools.")

        # 4. Prepare conversation
        messages = [
            {
                "role": "system",
                "content": llm.system_prompt
            },
            {
                "role": "user",
                "content": "Create a note named ideas.txt containing "
                           "three ideas for AI projects."
            }
        ]

        # 5. Send request and tools to Ollama
        response = llm.generate_response(
            messages,
            tools=ollama_tools
        )

        # 6. Inspect LLM response
        print("\n========== LLM RESPONSE ==========")

        print("Content:", response.content)

        print("\n========== TOOL CALLS ==========")

        if response.tool_calls:

            for tool_call in response.tool_calls:

                print("Tool:", tool_call.function.name)
                print("Arguments:", tool_call.function.arguments)

        else:
            print("No tool calls generated.")

    except Exception as error:
        print("Error:", error)

    finally:
        await mcp_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())