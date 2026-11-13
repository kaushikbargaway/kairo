from copy import deepcopy


class ConversationManager:

    def __init__(self, llm, max_exchanges=10):

        self.llm = llm
        self.max_exchanges = max_exchanges

        self.messages = [
            {
                "role": "system",
                "content": self.llm.system_prompt
            }
        ]

    def send_message(self, user_input):

        user_message = {
            "role": "user",
            "content": user_input
        }

        self.messages.append(user_message)

        try:

            response = self.llm.generate_response(
                self.messages
            )

        except Exception:
            # Remove the unanswered user message
            self.messages.pop()
            raise

        assistant_message = {
            "role": "assistant",
            "content": response
        }

        self.messages.append(assistant_message)

        self._trim_history()

        return response

    def _trim_history(self):

        system_message = self.messages[0]

        recent_messages = self.messages[1:]

        max_messages = self.max_exchanges * 2

        if len(recent_messages) > max_messages:

            recent_messages = recent_messages[-max_messages:]

        self.messages = [
            system_message,
            *recent_messages
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