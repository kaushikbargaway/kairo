class ToolExecutor:

    def __init__(self, mcp_client, tool_registry, approval_callback=None):
        self.mcp_client = mcp_client
        self.tool_registry = tool_registry
        self.approval_callback = approval_callback

    def validate_arguments(self, tool, arguments):

        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a dictionary.")

        schema = tool.input_schema

        required = schema.get("required", [])
        properties = schema.get("properties", {})

        # Check for missing required arguments
        missing = [
            argument
            for argument in required
            if argument not in arguments
        ]

        if missing:
            raise ValueError(
                f"Missing required arguments: {missing}"
            )

        # Check for unexpected arguments
        unexpected = [
            argument
            for argument in arguments
            if argument not in properties
        ]

        if unexpected:
            raise ValueError(
                f"Unexpected arguments: {unexpected}"
            )

    async def execute(self, tool_name, arguments):

        # 1. Check whether the tool exists
        tool = self.tool_registry.get_tool(tool_name)

        if tool is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        # 2. Validate arguments
        self.validate_arguments(tool, arguments)

        # 3. Request approval for destructive operations
        if tool_name == "delete_note":

            if self.approval_callback is None:
                return "Deletion cancelled: approval handler is not configured."

            approved = self.approval_callback(tool_name, arguments)

            if not approved:
                return "Deletion cancelled by the user."

        # 4. Execute the MCP tool
        result = await self.mcp_client.call_tool(
            tool_name,
            arguments
        )

        return result