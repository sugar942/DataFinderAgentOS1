from app.models.db import get_connection


class OperationLogRepository:

    @staticmethod
    def add(username: str, user_type: str, action: str, detail: str = "", ip_address: str = ""):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO operation_logs (username, user_type, action, detail, ip_address) VALUES (?,?,?,?,?)",
                (username, user_type, action, detail, ip_address)
            )

    @staticmethod
    def get_recent(limit: int = 10):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM operation_logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    @staticmethod
    def get_all(page: int = 1, limit: int = 20, keyword: str = ""):
        offset = (page - 1) * limit
        with get_connection() as conn:
            if keyword:
                count = conn.execute(
                    "SELECT COUNT(*) FROM operation_logs WHERE username LIKE ? OR detail LIKE ?",
                    (f"%{keyword}%", f"%{keyword}%")
                ).fetchone()[0]
                rows = conn.execute(
                    "SELECT * FROM operation_logs WHERE username LIKE ? OR detail LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?",
                    (f"%{keyword}%", f"%{keyword}%", limit, offset)
                ).fetchall()
            else:
                count = conn.execute("SELECT COUNT(*) FROM operation_logs").fetchone()[0]
                rows = conn.execute(
                    "SELECT * FROM operation_logs ORDER BY id DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                ).fetchall()
        return count, rows
