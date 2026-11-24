class ConversationSummarizer:

    def __init__(self, llm, max_input_messages: int = 40):
        if (
            not isinstance(max_input_messages, int)
            or isinstance(max_input_messages, bool)
            or max_input_messages <= 0
        ):
            raise ValueError(
                "max_input_messages must be a positive integer."
            )

        self.llm = llm
        self.max_input_messages = max_input_messages

    @staticmethod
    def _format_messages(messages: list[dict]) -> str:
        """Format conversation messages, including tool interactions."""
        formatted_messages = []

        for message in messages:
            if not isinstance(message, dict):
                continue

            role = message.get("role", "unknown")
            content = message.get("content", "")

            if role == "system":
                continue

            if role == "assistant":
                if content:
                    formatted_messages.append(
                        f"Assistant: {content}"
                    )

                tool_calls = message.get("tool_calls", [])

                for tool_call in tool_calls:
                    if not isinstance(tool_call, dict):
                        continue

                    function = tool_call.get("function", {})
                    if not isinstance(function, dict):
                        continue

                    tool_name = function.get("name", "unknown")
                    arguments = function.get("arguments", {})

                    formatted_messages.append(
                        f"Assistant called tool '{tool_name}' "
                        f"with arguments: {arguments}"
                    )

            elif role == "tool":
                tool_name = message.get("tool_name", "unknown")

                formatted_messages.append(
                    f"Tool result ({tool_name}): {content}"
                )

            elif role == "user" and content:
                formatted_messages.append(
                    f"User: {content}"
                )

            elif content:
                formatted_messages.append(
                    f"{role.capitalize()}: {content}"
                )

        return "\n".join(formatted_messages)

    def summarize(
        self,
        messages,
        existing_summary=""
    ):

        if not isinstance(messages, list):
            raise ValueError("Messages must be a list.")

        if not isinstance(existing_summary, str):
            raise ValueError("Existing summary must be a string.")

        if not messages and not existing_summary.strip():
            return ""

        # Limit the number of messages sent to the model.
        selected_messages = messages[
            -self.max_input_messages:
        ]

        conversation_text = self._format_messages(
            selected_messages
        )

        if not conversation_text.strip() and not existing_summary.strip():
            return ""

        prompt = f"""
You are KAIRO's conversation summarization engine.

Your task is to maintain a useful and accurate summary
of an ongoing conversation.

An existing summary may be provided along with newer
conversation messages.

You must combine the existing summary with the new
conversation information into one updated summary.

IMPORTANT INSTRUCTIONS:

1. Preserve important facts and information.
2. Preserve project details, technical decisions,
   technologies, and implementation progress.
3. Preserve explicitly stated user preferences.
4. Preserve problems encountered and solutions attempted.
5. Identify unresolved issues and pending tasks.
6. Preserve important decisions and their reasoning.
7. Remove greetings, repetitive statements, and irrelevant
   conversational details.
8. Do not invent facts or assume missing information.
9. Do not convert uncertain information into confirmed facts.
10. Avoid repeating information unnecessarily.
11. Keep the summary concise but sufficiently detailed
    for future conversation continuity.

Use the following structure:

## General Context
Important background information.

## Key Information
Important facts, preferences, and requirements.

## Projects and Technical Details
Project progress, technologies, implementation decisions,
and relevant technical information.

## Problems and Decisions
Issues discussed, solutions attempted, and decisions made.

## Pending Tasks
Unresolved questions, unfinished work, and next steps.

If a section has no relevant information, omit it.

Do not include introductory statements or explanations.
Return only the updated summary.

EXISTING SUMMARY:

{existing_summary if existing_summary.strip() else "No previous summary available."}

NEW CONVERSATION MESSAGES:

{conversation_text}
"""

        response = self.llm.generate_response(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Support both plain string responses and
        # Ollama response objects.

        if isinstance(response, str):
            summary = response

        else:
            summary = getattr(response, "content", None)

        if not isinstance(summary, str) or not summary.strip():
            raise ValueError(
                "The LLM returned an empty or invalid summary."
            )

        return summary.strip()