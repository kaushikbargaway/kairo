import asyncio

from ollama_client.client import KairoLLM
from conversation.manager import ConversationManager

from client.mcp_client import MCPToolClient
from agent.orchestrator import AgentOrchestrator

def approve_tool_execution(tool_name, arguments):

    if tool_name == "delete_note":
        filename = arguments.get("filename", "unknown file")

        print(f"\n[KAIRO] Permission required!")
        print(f"[KAIRO] You are about to delete: {filename}")

        confirmation = input("Approve deletion? (yes/no): ").strip().lower()

        return confirmation in ["yes", "y"]

    return True

async def main():

    # Initialize LLM
    ai = KairoLLM()

    # Initialize MCP Client
    mcp_client = MCPToolClient()

    try:

        # Connect to MCP Server
        await mcp_client.connect()

        # Initialize Agent Orchestrator
        agent = AgentOrchestrator(
            llm=ai,
            mcp_client=mcp_client,
            approval_callback=approve_tool_execution
        )

        # Initialize Conversation Manager
        conversation = ConversationManager(
            llm=ai,
            agent=agent,
            max_exchanges=10
        )

        print("\n================================")
        print("       KAIRO AI ASSISTANT")
        print("================================")

        print(f"Model: {ai.model}")
        print("Conversation Memory: Enabled")
        print("MCP Integration: Enabled")

        print("\nAvailable Commands:")
        print("/reset  - Reset conversation")
        print("/history - View conversation history")
        print("/exit   - Exit KAIRO")

        print("\nKAIRO is ready!\n")

        while True:

            user_input = input("You: ").strip()

            if not user_input:
                continue

            command = user_input.lower()

            if command == "/exit":

                print("\nKAIRO: Goodbye!")
                break

            elif command == "/reset":

                conversation.reset_conversation()

                print("\nKAIRO: Conversation reset successfully!\n")
                continue

            elif command == "/history":

                history = conversation.get_history()

                print("\n--- Conversation History ---")

                for message in history:

                    if message["role"] == "system":
                        continue

                    role = message["role"].upper()

                    if message.get("tool_calls"):

                        tool_names = [
                            call["function"]["name"]
                            for call in message["tool_calls"]
                        ]

                        print(f"\n{role}: Requested tools {tool_names}")

                    else:

                        print(f"\n{role}: {message['content']}")

                print("\n----------------------------\n")
                continue

            try:

                response = await conversation.send_message(
                    user_input
                )

                print(f"\nKAIRO: {response}\n")

            except Exception as error:

                print(f"\nKAIRO Error: {error}\n")

    except ConnectionError as error:
        print(f"\nKAIRO Error: {error}")
        print("KAIRO could not start because the MCP server is unavailable.")

    finally:

        await mcp_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())