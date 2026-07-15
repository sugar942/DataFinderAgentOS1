import sqlite3
from app.models.db import get_connection


class RoleRepository:

    @staticmethod
    def get_all():
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM roles ORDER BY id"
            ).fetchall()

    @staticmethod
    def get_by_id(role_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM roles WHERE id=?", (role_id,)
            ).fetchone()

    @staticmethod
    def create(name: str, code: str, description: str = "", status: int = 1) -> bool:
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO roles (name, code, description, status) VALUES (?,?,?,?)",
                    (name, code, description, status)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(role_id: int, name: str, code: str, description: str = "", status: int = 1) -> bool:
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE roles SET name=?, code=?, description=?, status=? WHERE id=?",
                    (name, code, description, status, role_id)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(role_id: int) -> bool:
        with get_connection() as conn:
            conn.execute("DELETE FROM role_functions WHERE role_id=?", (role_id,))
            conn.execute("DELETE FROM role_menus WHERE role_id=?", (role_id,))
            conn.execute("DELETE FROM user_roles WHERE role_id=?", (role_id,))
            conn.execute("DELETE FROM roles WHERE id=?", (role_id,))
            return True

    @staticmethod
    def get_role_functions(role_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT function_id FROM role_functions WHERE role_id=?", (role_id,)
            ).fetchall()
            return [r["function_id"] for r in rows]

    @staticmethod
    def get_role_menus(role_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT menu_id FROM role_menus WHERE role_id=?", (role_id,)
            ).fetchall()
            return [r["menu_id"] for r in rows]

    @staticmethod
    def assign_functions(role_id: int, function_ids: list):
        with get_connection() as conn:
            conn.execute("DELETE FROM role_functions WHERE role_id=?", (role_id,))
            for fid in function_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO role_functions (role_id, function_id) VALUES (?,?)",
                    (role_id, fid)
                )

    @staticmethod
    def assign_menus(role_id: int, menu_ids: list):
        with get_connection() as conn:
            conn.execute("DELETE FROM role_menus WHERE role_id=?", (role_id,))
            for mid in menu_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO role_menus (role_id, menu_id) VALUES (?,?)",
                    (role_id, mid)
                )
