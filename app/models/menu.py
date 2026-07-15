from app.models.db import get_connection


class MenuRepository:

    @staticmethod
    def get_all():
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM menus ORDER BY sort, id"
            ).fetchall()

    @staticmethod
    def get_by_id(menu_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM menus WHERE id=?", (menu_id,)
            ).fetchone()

    @staticmethod
    def get_by_parent(parent_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM menus WHERE parent_id=? ORDER BY sort, id",
                (parent_id,)
            ).fetchall()

    @staticmethod
    def create(name: str, icon: str = "", url: str = "",
               parent_id: int = 0, sort: int = 0, status: int = 1) -> bool:
        import sqlite3
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO menus (name, icon, url, parent_id, sort, status) VALUES (?,?,?,?,?,?)",
                    (name, icon, url, parent_id, sort, status)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(menu_id: int, name: str, icon: str = "", url: str = "",
               parent_id: int = 0, sort: int = 0, status: int = 1) -> bool:
        import sqlite3
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE menus SET name=?, icon=?, url=?, parent_id=?, sort=?, status=? WHERE id=?",
                    (name, icon, url, parent_id, sort, status, menu_id)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(menu_id: int) -> bool:
        with get_connection() as conn:
            conn.execute("DELETE FROM role_menus WHERE menu_id=?", (menu_id,))
            conn.execute("DELETE FROM menus WHERE id=?", (menu_id,))
            return True
