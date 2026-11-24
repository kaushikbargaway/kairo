import re

from difflib import SequenceMatcher

from memory.models import Memory


class MemoryProcessor:

    def __init__(
        self,
        store,
        similarity_threshold=0.96
    ):
        self.store = store
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def _normalize(content):

        content = content.lower().strip()

        content = re.sub(
            r"[^\w\s]",
            "",
            content
        )

        content = re.sub(
            r"\s+",
            " ",
            content
        )

        return content

    def _is_duplicate(self, new_memory, existing_memory):

        # Memories from different categories should not
        # automatically be considered duplicates.
        if new_memory.category != existing_memory.category:
            return False

        new_content = self._normalize(new_memory.content)

        existing_content = self._normalize(
            existing_memory.content
        )

        if new_content == existing_content:
            return True

        similarity = SequenceMatcher(
            None,
            new_content,
            existing_content
        ).ratio()

        return similarity >= self.similarity_threshold

    def _merge_duplicate(self, existing_memory, new_memory):

        # Preserve the existing content because similarity
        # alone does not establish that the new content is
        # a more accurate replacement.
        existing_memory.importance = max(
            existing_memory.importance,
            new_memory.importance
        )

        existing_memory.confidence = max(
            existing_memory.confidence,
            new_memory.confidence
        )

        # Preserve the latest source conversation.
        if new_memory.source_conversation_id:
            existing_memory.source_conversation_id = (
                new_memory.source_conversation_id
            )

        self.store.update_memory(existing_memory)

    def process_memory(self, memory, existing_memories=None):

        if not isinstance(memory, Memory):
            raise TypeError("Expected a Memory object.")

        if existing_memories is None:
            existing_memories = self.store.get_all_memories()

        for existing_memory in existing_memories:

            if self._is_duplicate(memory, existing_memory):

                self._merge_duplicate(
                    existing_memory,
                    memory
                )

                return "duplicate"

        self.store.add_memory(memory)

        return "added"

    def process_memories(self, memories):

        if not isinstance(memories, list):
            raise ValueError("Memories must be provided as a list.")

        existing_memories = self.store.get_all_memories()

        results = {
            "added": 0,
            "duplicates": 0,
            "invalid": 0
        }

        for memory in memories:

            if not isinstance(memory, Memory):
                results["invalid"] += 1
                continue

            result = self.process_memory(
                memory,
                existing_memories
            )

            if result == "added":
                results["added"] += 1
                existing_memories.append(memory)

            elif result == "duplicate":
                results["duplicates"] += 1

        return results