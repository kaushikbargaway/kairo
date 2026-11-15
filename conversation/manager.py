from copy import deepcopy


class ConversationManager:

    def __init__(
        self,
        llm,
        agent,
        max_exchanges=10,
        store=None,
        conversation_id=None
    ):
        self.llm = llm
        self.agent = agent
        self.max_exchanges = max_exchanges
        self.store = store

        self.messages = [
            {"role": "system", "content": self.llm.system_prompt}
        ]

        self.conversation_id = None

        if self.store:
            if conversation_id:
                self._load_conversation(conversation_id)
            else:
                self._create_conversation()

    def _create_conversation(self):
        self.conversation_id = self.store.create_conversation()

    def _load_conversation(self, conversation_id):
        conversation = self.store.get_conversation(conversation_id)

        if conversation is None:
            raise KeyError("Conversation not found.")

        self.conversation_id = conversation_id

        saved_messages = self.store.load_messages(conversation_id)

        self.messages = [
            {"role": "system", "content": self.llm.system_prompt},
            *saved_messages
        ]

    def _persist_conversation(self):
        if self.store and self.conversation_id:
            # System prompt is reconstructed when loading.
            self.store.save_messages(
                self.conversation_id,
                self.messages[1:]
            )

    async def send_message(self, user_input):

        original_length = len(self.messages)

        is_first_message = not any(
            message["role"] == "user"
            for message in self.messages[1:]
        )

        user_message = {
            "role": "user",
            "content": user_input
        }

        self.messages.append(user_message)

        try:
            response = await self.agent.process_request(self.messages)

        except Exception:
            del self.messages[original_length:]
            raise

        self._trim_history()

        self._persist_conversation()

        if self.store and self.conversation_id and is_first_message:

            title = self._generate_title(user_input)

            self.store.update_title(
                self.conversation_id,
                title
            )

        return response

    def _trim_history(self):
        system_message = self.messages[0]
        conversation_messages = self.messages[1:]

        exchanges = []
        current_exchange = []

        for message in conversation_messages:
            if message["role"] == "user":
                if current_exchange:
                    exchanges.append(current_exchange)

                current_exchange = [message]

            else:
                current_exchange.append(message)

        if current_exchange:
            exchanges.append(current_exchange)

        recent_exchanges = exchanges[-self.max_exchanges:]

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
            {"role": "system", "content": self.llm.system_prompt}
        ]

        if self.store:
            # Start a new conversation without deleting the old one.
            self._create_conversation()

    def get_history(self):
        return deepcopy(self.messages)

    @staticmethod
    def _generate_title(user_input, max_length=48):

        title = " ".join(user_input.split())

        if len(title) > max_length:
            title = title[:max_length - 3].rstrip() + "..."

        return title