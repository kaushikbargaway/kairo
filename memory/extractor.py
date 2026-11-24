import json

from memory.models import Memory, MemoryCategory


class MemoryExtractor:

    def __init__(
        self,
        llm,
        max_memories=10,
        max_input_messages=20
    ):
        self.llm = llm
        self.max_memories = max_memories
        self.max_input_messages = max_input_messages

    def extract(self, messages, conversation_id=None):

        user_messages = [
            message["content"]
            for message in messages
            if (
                message.get("role") == "user"
                and isinstance(message.get("content"), str)
                and message["content"].strip()
            )
        ]

        if not user_messages:
            return []

        # Process only the most recent user messages.
        user_messages = user_messages[-self.max_input_messages:]

        conversation_data = json.dumps(
            user_messages,
            ensure_ascii=False,
            indent=2
        )

        prompt = f"""
Analyze the following user conversation messages and extract
useful information that should be remembered for future conversations.

CONVERSATION MESSAGES:
{conversation_data}

EXTRACTION RULES:

1. Extract only information explicitly stated by the user.
2. Do not treat assistant-generated statements as user facts.
3. Prefer stable facts, preferences, ongoing projects,
   professional information and educational information.
4. Ignore greetings, temporary questions, casual remarks
   and information with little future value.
5. Do not invent information or make assumptions.
6. Do not extract passwords, API keys, authentication tokens,
   government identification numbers or other secrets.
7. Do not extract sensitive personal information.
8. Avoid creating multiple memories containing the same information.
9. Keep each memory concise and independently understandable.
10. Return no more than {self.max_memories} memories.

AVAILABLE CATEGORIES:

- personal
- project
- professional
- education
- preference
- general

IMPORTANCE:
A number between 0.0 and 1.0.

CONFIDENCE:
A number between 0.0 and 1.0 representing how explicitly
the user stated the information.

RETURN STRICT JSON ONLY.

Required JSON structure:

{{
    "memories": [
        {{
            "content": "A concise fact to remember",
            "category": "project",
            "importance": 0.9,
            "confidence": 1.0
        }}
    ]
}}

If no useful information is found, return:

{{
    "memories": []
}}
"""

        response = self.llm.generate_response(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return self._parse_response(
            response.content,
            conversation_id
        )

    def _parse_response(self, response_text, conversation_id=None):

        if not isinstance(response_text, str):
            return []

        response_text = response_text.strip()

        try:
            data = json.loads(response_text)

        except json.JSONDecodeError:

            # Attempt to recover JSON if the model
            # includes additional text around the response.
            start = response_text.find("{")
            end = response_text.rfind("}")

            if start == -1 or end == -1 or end < start:
                return []

            try:
                data = json.loads(response_text[start:end + 1])

            except json.JSONDecodeError:
                return []

        if not isinstance(data, dict):
            return []

        extracted_memories = data.get("memories", [])

        if not isinstance(extracted_memories, list):
            return []

        memories = []

        for item in extracted_memories[:self.max_memories]:

            if not isinstance(item, dict):
                continue

            try:
                memory = Memory(
                    content=item["content"],
                    category=MemoryCategory(item["category"]),
                    importance=float(item["importance"]),
                    confidence=float(item["confidence"]),
                    source="conversation",
                    source_conversation_id=conversation_id
                )

                memories.append(memory)

            except (KeyError, ValueError, TypeError):
                continue

        return memories