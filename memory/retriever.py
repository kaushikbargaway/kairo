import math

from memory.models import Memory


class MemoryRetriever:

    def __init__(
        self,
        store,
        embedding_engine,
        similarity_threshold=0.35
    ):

        self.store = store
        self.embedding_engine = embedding_engine
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def cosine_similarity(vector_a, vector_b):

        if len(vector_a) != len(vector_b):
            raise ValueError(
                "Embedding dimensions do not match."
            )

        dot_product = sum(
            a * b
            for a, b in zip(vector_a, vector_b)
        )

        magnitude_a = math.sqrt(
            sum(a * a for a in vector_a)
        )

        magnitude_b = math.sqrt(
            sum(b * b for b in vector_b)
        )

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (
            magnitude_a * magnitude_b
        )

    def index_memory(self, memory):

        if not isinstance(memory, Memory):
            raise TypeError("Expected a Memory object.")

        embedding = self.embedding_engine.embed(
            memory.content
        )

        self.store.save_embedding(
            memory.memory_id,
            embedding,
            self.embedding_engine.model
        )

    def index_pending_memories(self):

        memories = self.store.get_memories_without_embeddings(
            self.embedding_engine.model
        )

        if not memories:
            return 0

        embeddings = self.embedding_engine.embed_batch(
            [memory.content for memory in memories]
        )

        for memory, embedding in zip(memories, embeddings):

            self.store.save_embedding(
                memory.memory_id,
                embedding,
                self.embedding_engine.model
            )

        return len(memories)

    def retrieve(
        self,
        query,
        top_k=5,
        similarity_threshold=None
    ):

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold

        query_embedding = self.embedding_engine.embed(query)

        records = self.store.get_embedding_records(
            self.embedding_engine.model
        )

        results = []

        for record in records:

            memory = record["memory"]
            memory_embedding = record["embedding"]

            similarity = self.cosine_similarity(
                query_embedding,
                memory_embedding
            )

            if similarity >= similarity_threshold:

                results.append({
                    "memory": memory,
                    "similarity": similarity
                })

        results.sort(
            key=lambda item: item["similarity"],
            reverse=True
        )

        results = results[:top_k]

        for result in results:

            self.store.update_access_time(
                result["memory"].memory_id
            )

        return results