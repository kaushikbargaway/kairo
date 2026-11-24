from copy import deepcopy


class ConversationManager:

    def __init__(
        self,
        llm,
        agent,
        max_exchanges=10,
        store=None,
        conversation_id=None,
        memory_manager=None
    ):

        self.llm = llm
        self.agent = agent
        self.max_exchanges = max_exchanges
        self.store = store
        self.memory_manager = memory_manager

        self.messages = [
            {
                "role": "system",
                "content": self.llm.system_prompt
            }
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

        conversation = self.store.get_conversation(
            conversation_id
        )

        if conversation is None:
            raise KeyError("Conversation not found.")

        self.conversation_id = conversation_id

        saved_messages = self.store.load_messages(
            conversation_id
        )

        self.messages = [
            {
                "role": "system",
                "content": self.llm.system_prompt
            },
            *saved_messages
        ]

    def _persist_conversation(self):

        if self.store and self.conversation_id:

            self.store.save_messages(
                self.conversation_id,
                self.messages[1:]
            )

    def _build_request_messages(self, user_input):

        request_messages = deepcopy(self.messages)

        if self.memory_manager is None:
            return request_messages

        try:

            memory_context = self.memory_manager.build_context(
                query=user_input,
                top_k=5
            )

            if memory_context:

                request_messages[0]["content"] += (
                    "\n\n"
                    + memory_context
                )

        except Exception as error:

            print(
                f"\n[KAIRO Memory] Retrieval unavailable: {error}"
            )

        return request_messages

    def _learn_from_message(self, user_input):

        if self.memory_manager is None:
            return

        try:

            results = self.memory_manager.learn(
                messages=[
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                conversation_id=self.conversation_id
            )

            if results["added"] > 0:

                print(
                    f"\n[KAIRO Memory] "
                    f"Learned {results['added']} new memories."
                )

        except Exception as error:

            print(
                f"\n[KAIRO Memory] Learning unavailable: {error}"
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

            # Build a temporary request context containing
            # relevant long-term memories.
            request_messages = self._build_request_messages(
                user_input
            )

            # Process the request through the existing agent.
            response = await self.agent.process_request(
                request_messages
            )

        except Exception:

            del self.messages[original_length:]
            raise

        # Restore the original system prompt so retrieved
        # memories are never persisted in conversation history.
        request_messages[0]["content"] = self.llm.system_prompt

        self.messages = request_messages

        # Maintain existing conversation history behaviour.
        self._trim_history()

        self._persist_conversation()

        # Generate the conversation title when appropriate.
        if (
            self.store
            and self.conversation_id
            and is_first_message
        ):

            title = self._generate_title(user_input)

            self.store.update_title(
                self.conversation_id,
                title
            )

        # Extract useful information from the latest user message.
        # Memory failures must not interrupt normal conversation.
        self._learn_from_message(user_input)

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
            {
                "role": "system",
                "content": self.llm.system_prompt
            }
        ]

        if self.store:
            self._create_conversation()

    def get_history(self):

        return deepcopy(self.messages)

    @staticmethod
    def _generate_title(user_input, max_length=48):

        title = " ".join(user_input.split())

        if len(title) > max_length:
            title = title[:max_length - 3].rstrip() + "..."

        return title