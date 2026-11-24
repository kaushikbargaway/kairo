import json
import sqlite3

from pathlib import Path
from contextlib import contextmanager

from memory.models import Memory, MemoryCategory, current_timestamp


class MemoryStore:

    def __init__(self, db_path="data/kairo.db"):

        self.db_path = str(db_path)

        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(
                parents=True,
                exist_ok=True
            )

        self._initialize_database()

    @contextmanager
    def _connection(self):

        connection = sqlite3.connect(
            self.db_path,
            timeout=10
        )

        connection.row_factory = sqlite3.Row

        try:
            yield connection
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def _initialize_database(self):

        with self._connection() as connection:

            connection.executescript("""

                CREATE TABLE IF NOT EXISTS memories (

                    memory_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_conversation_id TEXT,

                    importance REAL NOT NULL
                        CHECK (importance BETWEEN 0 AND 1),

                    confidence REAL NOT NULL
                        CHECK (confidence BETWEEN 0 AND 1),

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_accessed_at TEXT,
                    metadata_json TEXT NOT NULL,

                    embedding_json TEXT,
                    embedding_model TEXT

                );

                CREATE INDEX IF NOT EXISTS idx_memories_category
                ON memories(category);

                CREATE INDEX IF NOT EXISTS idx_memories_updated_at
                ON memories(updated_at);

            """)

            # Migrate databases created by earlier versions.
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(memories)"
                ).fetchall()
            }

            if "embedding_json" not in columns:
                connection.execute(
                    "ALTER TABLE memories ADD COLUMN embedding_json TEXT"
                )

            if "embedding_model" not in columns:
                connection.execute(
                    "ALTER TABLE memories ADD COLUMN embedding_model TEXT"
                )

    @staticmethod
    def _row_to_memory(row):

        if row is None:
            return None

        data = dict(row)

        data["metadata"] = json.loads(
            data.pop("metadata_json")
        )

        data.pop("embedding_json", None)
        data.pop("embedding_model", None)

        return Memory.from_dict(data)

    def add_memory(self, memory):

        if not isinstance(memory, Memory):
            raise TypeError("Expected a Memory object.")

        with self._connection() as connection:

            connection.execute(
                """
                INSERT INTO memories (
                    memory_id, content, category, source,
                    source_conversation_id, importance,
                    confidence, created_at, updated_at,
                    last_accessed_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.memory_id,
                    memory.content,
                    memory.category.value,
                    memory.source,
                    memory.source_conversation_id,
                    memory.importance,
                    memory.confidence,
                    memory.created_at,
                    memory.updated_at,
                    memory.last_accessed_at,
                    json.dumps(memory.metadata, ensure_ascii=False)
                )
            )

        return memory.memory_id

    def get_memory(self, memory_id):

        with self._connection() as connection:

            row = connection.execute(
                """
                SELECT *
                FROM memories
                WHERE memory_id = ?
                """,
                (memory_id,)
            ).fetchone()

        return self._row_to_memory(row)

    def get_all_memories(self):

        with self._connection() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM memories
                ORDER BY updated_at DESC
                """
            ).fetchall()

        return [
            self._row_to_memory(row)
            for row in rows
        ]

    def update_memory(self, memory):

        if not isinstance(memory, Memory):
            raise TypeError("Expected a Memory object.")

        memory.updated_at = current_timestamp()

        with self._connection() as connection:

            cursor = connection.execute(
                """
                UPDATE memories
                SET content = ?,
                    category = ?,
                    source = ?,
                    source_conversation_id = ?,
                    importance = ?,
                    confidence = ?,
                    updated_at = ?,
                    last_accessed_at = ?,
                    metadata_json = ?,
                    embedding_json = NULL,
                    embedding_model = NULL
                WHERE memory_id = ?
                """,
                (
                    memory.content,
                    memory.category.value,
                    memory.source,
                    memory.source_conversation_id,
                    memory.importance,
                    memory.confidence,
                    memory.updated_at,
                    memory.last_accessed_at,
                    json.dumps(memory.metadata, ensure_ascii=False),
                    memory.memory_id
                )
            )

            if cursor.rowcount == 0:
                raise KeyError("Memory not found.")

        return True

    def delete_memory(self, memory_id):

        with self._connection() as connection:

            cursor = connection.execute(
                """
                DELETE FROM memories
                WHERE memory_id = ?
                """,
                (memory_id,)
            )

            return cursor.rowcount > 0

    def search_by_category(self, category):

        if isinstance(category, str):
            category = MemoryCategory(category)

        with self._connection() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM memories
                WHERE category = ?
                ORDER BY updated_at DESC
                """,
                (category.value,)
            ).fetchall()

        return [
            self._row_to_memory(row)
            for row in rows
        ]

    def update_access_time(self, memory_id):

        timestamp = current_timestamp()

        with self._connection() as connection:

            cursor = connection.execute(
                """
                UPDATE memories
                SET last_accessed_at = ?
                WHERE memory_id = ?
                """,
                (timestamp, memory_id)
            )

            return cursor.rowcount > 0

    def save_embedding(self, memory_id, embedding, model):

        with self._connection() as connection:

            cursor = connection.execute(
                """
                UPDATE memories
                SET embedding_json = ?,
                    embedding_model = ?
                WHERE memory_id = ?
                """,
                (
                    json.dumps(embedding),
                    model,
                    memory_id
                )
            )

            if cursor.rowcount == 0:
                raise KeyError("Memory not found.")

    def get_embedding_records(self, model):

        with self._connection() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM memories
                WHERE embedding_json IS NOT NULL
                  AND embedding_model = ?
                """,
                (model,)
            ).fetchall()

        records = []

        for row in rows:

            data = dict(row)

            embedding = json.loads(
                data.pop("embedding_json")
            )

            data.pop("embedding_model", None)

            memory_data = dict(data)

            memory_data["metadata"] = json.loads(
                memory_data.pop("metadata_json")
            )

            records.append({
                "memory": Memory.from_dict(memory_data),
                "embedding": embedding
            })

        return records

    def get_memories_without_embeddings(self, model):

        with self._connection() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM memories
                WHERE embedding_json IS NULL
                   OR embedding_model != ?
                """,
                (model,)
            ).fetchall()

        return [
            self._row_to_memory(row)
            for row in rows
        ]