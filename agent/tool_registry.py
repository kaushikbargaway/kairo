class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register_tools(self, mcp_tools):

        self.tools.clear()

        ollama_tools = []

        for tool in mcp_tools:

            # Store original MCP tool definition
            self.tools[tool.name] = tool

            # Convert MCP schema to Ollama format
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema
                }
            }

            ollama_tools.append(ollama_tool)

        return ollama_tools

    def get_tool(self, tool_name):

        return self.tools.get(tool_name)