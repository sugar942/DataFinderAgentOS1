from app.models.db import get_connection


class ConversationRepository:

    @staticmethod
    def create(user_id, title="新对话", model_name=""):
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO conversations (user_id, title, model_name) VALUES (?,?,?)",
                (user_id, title, model_name)
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_user(user_id, limit=50):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations WHERE user_id=? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(conversation_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id=?", (conversation_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update_title(conversation_id, title):
        with get_connection() as conn:
            conn.execute(
                "UPDATE conversations SET title=?, updated_at=datetime('now','localtime') WHERE id=?",
                (title, conversation_id)
            )

    @staticmethod
    def touch(conversation_id):
        with get_connection() as conn:
            conn.execute(
                "UPDATE conversations SET updated_at=datetime('now','localtime') WHERE id=?",
                (conversation_id,)
            )

    @staticmethod
    def delete(conversation_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM chat_messages WHERE conversation_id=?", (conversation_id,))
            conn.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))


class ChatMessageRepository:

    @staticmethod
    def add(conversation_id, role, content, tokens=0):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO chat_messages (conversation_id, role, content, tokens) VALUES (?,?,?,?)",
                (conversation_id, role, content, tokens)
            )

    @staticmethod
    def get_by_conversation(conversation_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE conversation_id=? ORDER BY created_at ASC",
                (conversation_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def count_by_conversation(conversation_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM chat_messages WHERE conversation_id=?",
                (conversation_id,)
            ).fetchone()
        return row[0] if row else 0
