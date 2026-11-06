from .app import mcp

# Register MCP capabilities
from . import tools
from . import resources
from . import prompts


if __name__ == "__main__":
    mcp.run()