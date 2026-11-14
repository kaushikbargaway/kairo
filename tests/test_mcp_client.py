import asyncio

from client.mcp_client import MCPToolClient


async def main():

    mcp_client = MCPToolClient()

    try:
        await mcp_client.connect()

        response = await mcp_client.list_tools()

        tools = response.tools

        print("\n========== AVAILABLE MCP TOOLS ==========\n")

        for tool in tools:

            print(f"Name: {tool.name}")
            print(f"Description: {tool.description}")
            print(f"Input Schema: {tool.input_schema}")

            print("------------------------------------------")

        print(f"\nTotal tools discovered: {len(tools)}")

    except Exception as error:
        print(f"Error: {error}")

    finally:
        await mcp_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())