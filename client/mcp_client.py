import sys

from mcp import Client, StdioServerParameters


class MCPToolClient:

    def __init__(self):

        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "servers.notepad.server"]
        )

        self.client_context = None
        self.client = None

    async def connect(self):
        context = Client(self.server_params)

        try:
            client = await context.__aenter__()

        except Exception as error:
            self.client = None
            self.client_context = None

            raise ConnectionError(
                "Failed to connect to KAIRO MCP Server. "
                "Please check whether the server is available."
            ) from error

        self.client_context = context
        self.client = client

        print("Connected to KAIRO MCP Server!")

    async def disconnect(self):
        if self.client_context is None:
            return

        context = self.client_context

        self.client_context = None
        self.client = None

        await context.__aexit__(None, None, None)

        print("Disconnected from MCP Server.")

    async def reconnect(self):
        print("\n[KAIRO] Attempting to reconnect to MCP Server...")

        # Close the existing connection, if possible
        try:
            await self.disconnect()

        except Exception as error:
            print(f"[KAIRO] Warning during connection cleanup: {error}")
            self.client = None
            self.client_context = None

        # Establish a fresh connection
        await self.connect()

    async def list_tools(self):

        if not self.client:
            raise RuntimeError("MCP client is not connected.")

        return await self.client.list_tools()

    async def call_tool(self, tool_name, arguments):

        if not self.client:
            raise RuntimeError("MCP client is not connected.")

        return await self.client.call_tool(
            tool_name,
            arguments
        )