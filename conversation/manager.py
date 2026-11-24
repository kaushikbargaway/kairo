from copy import deepcopy

from conversation.summarizer import ConversationSummarizer


class ConversationManager:

    def __init__(
        self,
        llm,
        agent,
        max_exchanges=10,
        store=None,
        conversation_id=None,
        memory_manager=None,
        summarizer=None
    ):

        if (
            not isinstance(max_exchanges, int)
            or isinstance(max_exchanges, bool)
            or max_exchanges < 1
        ):
            raise ValueError(
                "max_exchanges must be a positive integer."
            )

        self.llm = llm
        self.agent = agent
        self.max_exchanges = max_exchanges
        self.store = store
        self.memory_manager = memory_manager

        self.summarizer = (
            summarizer
            if summarizer is not None
            else ConversationSummarizer(llm)
        )

        self.conversation_id = None

        self.messages = [
            {
                "role": "system",
                "content": self.llm.system_prompt
            }
        ]

        self.summary = ""
        self.summary_message_count = 0

        if self.store:

            if conversation_id:

                self._load_conversation(conversation_id)

            else:

                self._create_conversation()

    # --------------------------------------------------
    # CONVERSATION INITIALIZATION
    # --------------------------------------------------

    def _create_conversation(self):

        self.conversation_id = (
            self.store.create_conversation()
        )

        self.messages = [
            {
                "role": "system",
                "content": self.llm.system_prompt
            }
        ]

        self.summary = ""
        self.summary_message_count = 0

    def _load_conversation(self, conversation_id):

        conversation = self.store.get_conversation(
            conversation_id
        )

        if conversation is None:
            raise KeyError("Conversation not found.")

        self.conversation_id = conversation_id

        stored_messages = self.store.load_messages(
            conversation_id
        )

        self.messages = [
            {
                "role": "system",
                "content": self.llm.system_prompt
            },
            *stored_messages
        ]

        self.summary = self.store.get_summary(
            conversation_id
        )

        self.summary_message_count = (
            self.store.get_summary_message_count(
                conversation_id
            )
        )

    # --------------------------------------------------
    # EXCHANGE MANAGEMENT
    # --------------------------------------------------

    @staticmethod
    def _split_exchanges(messages):

        exchanges = []
        current_exchange = []

        for message in messages:

            if message.get("role") == "user":

                if current_exchange:
                    exchanges.append(current_exchange)

                current_exchange = [message]

            else:

                if current_exchange:
                    current_exchange.append(message)

        if current_exchange:
            exchanges.append(current_exchange)

        return exchanges

    def _get_recent_exchanges(self, messages):

        exchanges = self._split_exchanges(messages)

        if not exchanges:
            return [], []

        if len(exchanges) <= self.max_exchanges:

            return [], exchanges

        older_exchanges = exchanges[
            :-self.max_exchanges
        ]

        recent_exchanges = exchanges[
            -self.max_exchanges:
        ]

        return older_exchanges, recent_exchanges

    # --------------------------------------------------
    # REQUEST CONTEXT CONSTRUCTION
    # --------------------------------------------------

    def _build_request_messages(self, user_input):

        conversation_messages = self.messages[1:]

        older_exchanges, recent_exchanges = (
            self._get_recent_exchanges(
                conversation_messages
            )
        )

        recent_messages = [
            message
            for exchange in recent_exchanges
            for message in exchange
        ]

        request_messages = [
            {
                "role": "system",
                "content": self.llm.system_prompt
            }
        ]

        # Inject conversation summary.

        if self.summary.strip():

            request_messages.append({
                "role": "system",
                "content": (
                    "CONVERSATION SUMMARY\n\n"
                    "The following is a summary of earlier "
                    "exchanges in this conversation.\n"
                    "Use it as background context when relevant.\n\n"
                    f"{self.summary}"
                )
            })

        # Inject semantic long-term memory.

        if self.memory_manager:

            try:

                memory_context = (
                    self.memory_manager.build_context(
                        user_input,
                        top_k=5
                    )
                )

                if memory_context:

                    request_messages.append({
                        "role": "system",
                        "content": (
                            "RELEVANT LONG-TERM MEMORY\n\n"
                            "The following information was "
                            "retrieved from previous interactions.\n"
                            "Use it only when relevant. "
                            "The current user message takes priority.\n\n"
                            f"{memory_context}"
                        )
                    })

            except Exception as error:

                print(
                    "[KAIRO Memory] Context retrieval failed: "
                    f"{error}"
                )

        # Append recent raw conversation messages.

        request_messages.extend(
            deepcopy(recent_messages)
        )

        return request_messages

    # --------------------------------------------------
    # AUTOMATIC CONVERSATION SUMMARIZATION
    # --------------------------------------------------

    def _update_summary(self):

        if not self.store:
            return

        conversation_messages = self.messages[1:]

        older_exchanges, _ = (
            self._get_recent_exchanges(
                conversation_messages
            )
        )

        if not older_exchanges:
            return

        older_messages = [
            message
            for exchange in older_exchanges
            for message in exchange
        ]

        # Nothing new needs summarizing.

        if (
            len(older_messages)
            <= self.summary_message_count
        ):
            return

        # Only summarize messages not already covered.

        new_messages = older_messages[
            self.summary_message_count:
        ]

        if not new_messages:
            return

        updated_summary = self.summarizer.summarize(
            new_messages,
            existing_summary=self.summary
        )

        if not updated_summary:
            return

        # Persist the new summary and its progress together.

        self.store.update_summary(
            self.conversation_id,
            updated_summary,
            len(older_messages)
        )

        self.summary = updated_summary

        self.summary_message_count = len(
            older_messages
        )

        print("[KAIRO] Conversation summary updated.")

    # --------------------------------------------------
    # LONG-TERM MEMORY LEARNING
    # --------------------------------------------------

    def _learn_from_message(self, user_input):

        if not self.memory_manager:
            return

        try:

            result = self.memory_manager.learn(
                messages=[
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                conversation_id=self.conversation_id
            )

            added = result.get("added", 0)

            if added:

                print(
                    f"[KAIRO Memory] Learned "
                    f"{added} new memory item(s)."
                )

        except Exception as error:

            print(
                "[KAIRO Memory] Learning failed: "
                f"{error}"
            )

    # --------------------------------------------------
    # CONVERSATION PERSISTENCE
    # --------------------------------------------------

    def _persist_conversation(self):

        if not self.store:
            return

        self.store.save_messages(
            self.conversation_id,
            self.messages[1:]
        )

    # --------------------------------------------------
    # CONVERSATION TITLE
    # --------------------------------------------------

    def _generate_title(self, user_input):

        title = " ".join(user_input.split())

        if len(title) > 48:
            title = title[:45] + "..."

        return title

    # --------------------------------------------------
    # MESSAGE PROCESSING
    # --------------------------------------------------

    async def send_message(self, user_input):

        if (
            not isinstance(user_input, str)
            or not user_input.strip()
        ):
            raise ValueError(
                "User input cannot be empty."
            )

        user_input = user_input.strip()

        original_length = len(self.messages)

        is_first_message = (
            len(self.messages) == 1
        )

        # Add the user's message to the complete transcript.

        self.messages.append({
            "role": "user",
            "content": user_input
        })

        try:

            # Construct optimized temporary context.

            request_messages = (
                self._build_request_messages(
                    user_input
                )
            )

            original_request_length = len(
                request_messages
            )

            # Process the request through the agent.

            response = await self.agent.process_request(
                request_messages
            )

            # Extract only newly generated messages.
            # Summary and memory context are never persisted.

            generated_messages = deepcopy(
                request_messages[
                    original_request_length:
                ]
            )

            # Add generated assistant/tool messages
            # to the complete conversation transcript.

            self.messages.extend(
                generated_messages
            )

            # Fallback in case the agent returns a response
            # without appending an assistant message.

            if (
                not generated_messages
                or generated_messages[-1].get("role") != "assistant"
                or generated_messages[-1].get("tool_calls")
            ):
                self.messages.append({
                    "role": "assistant",
                    "content": response
                })

        except Exception:

            # Roll back incomplete conversation messages.

            del self.messages[original_length:]

            raise

        # Persist the complete transcript.

        self._persist_conversation()

        # Generate the conversation title once.

        if is_first_message and self.store:

            title = self._generate_title(
                user_input
            )

            self.store.update_title(
                self.conversation_id,
                title
            )

        # Update the conversation summary.

        try:

            self._update_summary()

        except Exception as error:

            print(
                "[KAIRO Summary] Summary update failed: "
                f"{error}"
            )

        # Extract useful long-term memories.

        self._learn_from_message(
            user_input
        )

        return response

    # --------------------------------------------------
    # RESET / NEW CONVERSATION
    # --------------------------------------------------

    def reset_conversation(self):

        if self.store:

            self._create_conversation()

        else:

            self.messages = [
                {
                    "role": "system",
                    "content": self.llm.system_prompt
                }
            ]

            self.summary = ""
            self.summary_message_count = 0

    # --------------------------------------------------
    # HISTORY
    # --------------------------------------------------

    def get_history(self):

        return deepcopy(self.messages)