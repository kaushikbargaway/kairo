from ollama_client.client import KairoLLM
from conversation.manager import ConversationManager


def main():

    # Initialize LLM
    ai = KairoLLM()

    # Initialize Conversation Manager
    conversation = ConversationManager(ai)

    print("\n================================")
    print("       KAIRO AI ASSISTANT")
    print("================================")

    print(f"Model: {ai.model}")
    print("Conversation Memory: Enabled")

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

                print(f"\n{role}: {message['content']}")

            print("\n----------------------------\n")
            continue

        try:

            response = conversation.send_message(
                user_input
            )

            print(f"\nKAIRO: {response}\n")

        except Exception as e:

            print(f"\nKAIRO Error: {e}\n")


if __name__ == "__main__":
    main()