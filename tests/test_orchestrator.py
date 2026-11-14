import asyncio

from ollama_client.client import KairoLLM
from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator


async def main():

    # Initialize components
    llm = KairoLLM()
    mcp_client = MCPToolClient()

    try:
        # Connect to MCP server
        await mcp_client.connect()

        # Initialize Agent Orchestrator
        agent = AgentOrchestrator(
            llm=llm,
            mcp_client=mcp_client
        )

        # Prepare conversation
        messages = [
            {
                "role": "system",
                "content": llm.system_prompt
            },
            {
                "role": "user",
                "content": (
                    "Create a note named kairo_test.txt "
                    "containing: KAIRO successfully executed "
                    "its first orchestrated MCP operation."
                )
            }
        ]

        print("\n========== KAIRO AGENT TEST ==========\n")

        print("User: Create a test note.")

        # Process request through Agent
        response = await agent.process_request(messages)

        print("\n========== FINAL RESPONSE ==========\n")
        print("KAIRO:", response)

    except Exception as error:
        print(f"\nAgent Error: {error}")

    finally:
        await mcp_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())