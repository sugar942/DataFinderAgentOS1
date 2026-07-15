from app.models.db import get_connection


class FunctionRepository:

    @staticmethod
    def get_all():
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM functions ORDER BY sort, id"
            ).fetchall()

    @staticmethod
    def get_by_id(func_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM functions WHERE id=?", (func_id,)
            ).fetchone()

    @staticmethod
    def get_by_parent(parent_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM functions WHERE parent_id=? ORDER BY sort, id",
                (parent_id,)
            ).fetchall()

    @staticmethod
    def create(name: str, code: str, url: str = "", method: str = "GET",
               parent_id: int = 0, func_type: str = "menu", sort: int = 0,
               status: int = 1) -> bool:
        import sqlite3
        try:
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO functions (name, code, url, method, parent_id, type, sort, status)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (name, code, url, method, parent_id, func_type, sort, status)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(func_id: int, name: str, code: str, url: str = "", method: str = "GET",
               parent_id: int = 0, func_type: str = "menu", sort: int = 0,
               status: int = 1) -> bool:
        import sqlite3
        try:
            with get_connection() as conn:
                conn.execute(
                    """UPDATE functions SET name=?, code=?, url=?, method=?,
                       parent_id=?, type=?, sort=?, status=? WHERE id=?""",
                    (name, code, url, method, parent_id, func_type, sort, status, func_id)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(func_id: int) -> bool:
        with get_connection() as conn:
            conn.execute("DELETE FROM role_functions WHERE function_id=?", (func_id,))
            conn.execute("DELETE FROM functions WHERE id=?", (func_id,))
            return True
