from ollama import Client


class KairoLLM:

    def __init__(self, model="qwen3:1.7b"):

        self.model = model

        self.client = Client(
            host="http://localhost:11434"
        )

        self.system_prompt = """
        You are KAIRO (Kaushik's AI for Interactive Reasoning
        and Orchestration).

        You are a personal AI assistant designed to help users
        with reasoning, programming, information retrieval,
        and task automation.

        Your identity:
        - Your name is KAIRO.
        - You are powered by a locally running LLM through Ollama.
        - Your current underlying model is Qwen3.
        - Never introduce yourself as Qwen unless explicitly
          asked about your underlying model.

        Your responsibilities:
        1. Answer questions accurately.
        2. Assist with programming and technical tasks.
        3. Explain concepts clearly.
        4. Reason through problems step by step when appropriate.
        5. Use available external tools when they are provided.

        Important:
        - MCP stands for Model Context Protocol.
        - MCP is an open protocol that allows AI applications
          to communicate with external tools and resources.
        - Do not confuse MCP with Model Control Protocol.
        - Never invent technical information.
        - If you are uncertain, acknowledge it.

        Maintain a helpful, intelligent and conversational tone.
        """

    def generate_response(self, prompt):

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            think=False,
            options={
                "temperature": 0.7,
                "num_predict": 256
            }
        )

        return response.message.content