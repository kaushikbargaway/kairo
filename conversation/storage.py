import json
import sqlite3
import uuid

from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager


class ConversationStore:

    def __init__(self, db_path="data/kairo.db"):

        self.db_path = str(db_path)

        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(
                parents=True,
                exist_ok=True
            )

        self._initialize_database()

    @staticmethod
    def _timestamp():

        return datetime.now(timezone.utc).isoformat()

    @contextmanager
    def _connection(self):

        connection = sqlite3.connect(
            self.db_path,
            timeout=10
        )

        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA foreign_keys = ON")

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

                CREATE TABLE IF NOT EXISTS conversations (

                    conversation_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL

                );

                CREATE TABLE IF NOT EXISTS messages (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    conversation_id TEXT NOT NULL,

                    sequence INTEGER NOT NULL,

                    message_json TEXT NOT NULL,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations(conversation_id)
                        ON DELETE CASCADE,

                    UNIQUE (conversation_id, sequence)

                );

            """)

    def create_conversation(self, title="New conversation"):

        conversation_id = str(uuid.uuid4())

        timestamp = self._timestamp()

        with self._connection() as connection:

            connection.execute(
                """
                INSERT INTO conversations (
                    conversation_id,
                    title,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    title,
                    timestamp,
                    timestamp
                )
            )

        return conversation_id

    def save_messages(self, conversation_id, messages):

        if not isinstance(messages, list):
            raise ValueError("Messages must be a list.")

        # Serialize before modifying existing database records.
        serialized_messages = []

        for message in messages:

            if not isinstance(message, dict):
                raise ValueError(
                    "Every conversation message must be a dictionary."
                )

            serialized_messages.append(
                json.dumps(
                    message,
                    ensure_ascii=False
                )
            )

        timestamp = self._timestamp()

        with self._connection() as connection:

            conversation = connection.execute(
                """
                SELECT conversation_id
                FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,)
            ).fetchone()

            if conversation is None:
                raise KeyError("Conversation not found.")

            connection.execute(
                """
                DELETE FROM messages
                WHERE conversation_id = ?
                """,
                (conversation_id,)
            )

            connection.executemany(
                """
                INSERT INTO messages (
                    conversation_id,
                    sequence,
                    message_json,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        conversation_id,
                        index,
                        message,
                        timestamp
                    )
                    for index, message in enumerate(
                        serialized_messages
                    )
                ]
            )

            connection.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE conversation_id = ?
                """,
                (timestamp, conversation_id)
            )

    def load_messages(self, conversation_id):

        with self._connection() as connection:

            rows = connection.execute(
                """
                SELECT message_json
                FROM messages
                WHERE conversation_id = ?
                ORDER BY sequence ASC
                """,
                (conversation_id,)
            ).fetchall()

        return [
            json.loads(row["message_json"])
            for row in rows
        ]

    def get_conversation(self, conversation_id):

        with self._connection() as connection:

            row = connection.execute(
                """
                SELECT *
                FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,)
            ).fetchone()

        return dict(row) if row else None

    def list_conversations(self):

        with self._connection() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM conversations
                ORDER BY updated_at DESC
                """
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def delete_conversation(self, conversation_id):

        with self._connection() as connection:

            cursor = connection.execute(
                """
                DELETE FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,)
            )

            return cursor.rowcount > 0

    def update_title(self, conversation_id, title):

        if not isinstance(title, str) or not title.strip():
            raise ValueError("Conversation title cannot be empty.")

        timestamp = self._timestamp()

        with self._connection() as connection:

            cursor = connection.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE conversation_id = ?
                """,
                (title.strip(), timestamp, conversation_id)
            )

            if cursor.rowcount == 0:
                raise KeyError("Conversation not found.")
