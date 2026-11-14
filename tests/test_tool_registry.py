import asyncio

from client.mcp_client import MCPToolClient
from agent.tool_registry import ToolRegistry


async def main():

    mcp_client = MCPToolClient()
    registry = ToolRegistry()

    try:

        await mcp_client.connect()

        response = await mcp_client.list_tools()

        mcp_tools = response.tools

        ollama_tools = registry.register_tools(mcp_tools)

        print("\n========== OLLAMA TOOL DEFINITIONS ==========\n")

        for tool in ollama_tools:
            print(tool)

        print(f"\nTotal registered tools: {len(registry.tools)}")

    except Exception as error:
        print("Error:", error)

    finally:
        await mcp_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())