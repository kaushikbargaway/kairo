import asyncio

from client.mcp_client import MCPToolClient


async def main():

    mcp = MCPToolClient()

    try:
        # Initial connection
        await mcp.connect()

        # Disconnect
        await mcp.disconnect()

        # Reconnect
        await mcp.reconnect()

        # Verify available tools
        tools = await mcp.list_tools()

        print("\nAvailable MCP Tools:")

        for tool in tools.tools:
            print(f"- {tool.name}")

    finally:
        await mcp.disconnect()


if __name__ == "__main__":
    asyncio.run(main())