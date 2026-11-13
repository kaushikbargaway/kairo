from ollama_client.client import KairoLLM


def main():
    ai = KairoLLM()

    print("KAIRO is ready!")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("KAIRO: Goodbye!")
            break

        response = ai.generate_response(user_input)

        print(f"\nKAIRO: {response}\n")


if __name__ == "__main__":
    main()