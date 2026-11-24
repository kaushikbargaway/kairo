import math

from ollama import Client


class EmbeddingEngine:

    def __init__(
        self,
        client=None,
        model="all-minilm"
    ):
        self.model = model

        self.client = client or Client(
            host="http://localhost:11434"
        )

        self.embedding_dimension = None

    def embed(self, text):

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text cannot be empty.")

        response = self.client.embed(
            model=self.model,
            input=text
        )

        embeddings = response.embeddings

        if not embeddings or len(embeddings) != 1:
            raise RuntimeError(
                "Ollama returned an invalid embedding response."
            )

        embedding = self._validate_embedding(embeddings[0])

        self.embedding_dimension = len(embedding)

        return embedding

    def embed_batch(self, texts):

        if not isinstance(texts, (list, tuple)):
            raise TypeError("Input must be a list or tuple of texts.")

        if not texts:
            return []

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "Every input text must be a non-empty string."
            )

        response = self.client.embed(
            model=self.model,
            input=list(texts)
        )

        embeddings = response.embeddings

        if len(embeddings) != len(texts):
            raise RuntimeError(
                "Embedding count does not match input count."
            )

        validated_embeddings = [
            self._validate_embedding(embedding)
            for embedding in embeddings
        ]

        dimensions = {
            len(embedding)
            for embedding in validated_embeddings
        }

        if len(dimensions) != 1:
            raise RuntimeError(
                "Ollama returned embeddings with inconsistent dimensions."
            )

        self.embedding_dimension = dimensions.pop()

        return validated_embeddings

    @staticmethod
    def _validate_embedding(embedding):

        if not isinstance(embedding, (list, tuple)) or not embedding:
            raise RuntimeError("Invalid embedding returned by Ollama.")

        try:
            vector = [float(value) for value in embedding]

        except (TypeError, ValueError):
            raise RuntimeError(
                "Embedding contains invalid numerical values."
            ) from None

        if not all(math.isfinite(value) for value in vector):
            raise RuntimeError(
                "Embedding contains non-finite numerical values."
            )

        return vector

    def get_embedding_dimension(self):

        if self.embedding_dimension is None:
            self.embed("KAIRO embedding dimension detection.")

        return self.embedding_dimension