from copy import deepcopy


class ConversationManager:

    def __init__(self, llm, agent, max_exchanges=10):

        self.llm = llm
        self.agent = agent
        self.max_exchanges = max_exchanges

        self.messages = [
            {
                "role": "system",
                "content": self.llm.system_prompt
            }
        ]

    async def send_message(self, user_input):

        original_length = len(self.messages)

        user_message = {
            "role": "user",
            "content": user_input
        }

        self.messages.append(user_message)

        try:

            response = await self.agent.process_request(
                self.messages
            )

        except Exception:

            # Remove incomplete conversation messages
            del self.messages[original_length:]

            raise

        self._trim_history()

        return response

    def _trim_history(self):

        system_message = self.messages[0]
        conversation_messages = self.messages[1:]

        exchanges = []
        current_exchange = []

        for message in conversation_messages:

            # A new user message starts a new exchange
            if message["role"] == "user":

                if current_exchange:
                    exchanges.append(current_exchange)

                current_exchange = [message]

            else:
                current_exchange.append(message)

        # Include the final exchange
        if current_exchange:
            exchanges.append(current_exchange)

        # Retain the most recent complete exchanges
        recent_exchanges = exchanges[-self.max_exchanges:]

        # Flatten exchanges back into the message history
        self.messages = [
            system_message,
            *[
                message
                for exchange in recent_exchanges
                for message in exchange
            ]
        ]

    def reset_conversation(self):

        self.messages = [
            {
                "role": "system",
                "content": self.llm.system_prompt
            }
        ]

    def get_history(self):

        return deepcopy(self.messages)