import hashlib
import secrets
import sqlite3

from app.models.db import get_connection


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return dk.hex()


class AdminRepository:
    """管理员数据访问层 —— 面向 Controller 提供静态方法"""

    @staticmethod
    def create_admin(username: str, password: str, is_super: int = 1) -> bool:
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO admins (username, password_hash, salt, is_super) VALUES (?,?,?,?)",
                    (username, password_hash, salt.hex(), is_super)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_admin_by_username(username: str):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, salt, is_super FROM admins WHERE username=?",
                (username,)
            ).fetchone()
        return row

    @staticmethod
    def verify_admin(username: str, password: str) -> bool:
        row = AdminRepository.get_admin_by_username(username)
        if not row:
            return False
        salt = bytes.fromhex(row["salt"])
        return _hash_password(password, salt) == row["password_hash"]

    @staticmethod
    def get_all(page: int = 1, limit: int = 10, keyword: str = ""):
        offset = (page - 1) * limit
        with get_connection() as conn:
            base_query = """
                SELECT id, username, 1 AS is_admin, is_super, created_at
                FROM admins
                UNION ALL
                SELECT id, username, 0 AS is_admin, 0 AS is_super, created_at
                FROM users
            """
            if keyword:
                where = " WHERE username LIKE ?"
                count = conn.execute(
                    f"SELECT COUNT(*) FROM ({base_query}){where}",
                    (f"%{keyword}%",)
                ).fetchone()[0]
                rows = conn.execute(
                    f"SELECT * FROM ({base_query}){where} ORDER BY is_admin DESC, id LIMIT ? OFFSET ?",
                    (f"%{keyword}%", limit, offset)
                ).fetchall()
            else:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM ({base_query})"
                ).fetchone()[0]
                rows = conn.execute(
                    f"SELECT * FROM ({base_query}) ORDER BY is_admin DESC, id LIMIT ? OFFSET ?",
                    (limit, offset)
                ).fetchall()
        return count, rows

    @staticmethod
    def get_by_id(admin_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT id, username, is_super, created_at FROM admins WHERE id=?",
                (admin_id,)
            ).fetchone()

    @staticmethod
    def update_admin(admin_id: int, password: str = "", is_super: int = None) -> bool:
        with get_connection() as conn:
            if password:
                salt = secrets.token_bytes(16)
                password_hash = _hash_password(password, salt)
                if is_super is not None:
                    conn.execute(
                        "UPDATE admins SET password_hash=?, salt=?, is_super=? WHERE id=?",
                        (password_hash, salt.hex(), is_super, admin_id)
                    )
                else:
                    conn.execute(
                        "UPDATE admins SET password_hash=?, salt=? WHERE id=?",
                        (password_hash, salt.hex(), admin_id)
                    )
            elif is_super is not None:
                conn.execute(
                    "UPDATE admins SET is_super=? WHERE id=?",
                    (is_super, admin_id)
                )
            return True

    @staticmethod
    def delete_admin(admin_id: int) -> bool:
        with get_connection() as conn:
            conn.execute("DELETE FROM user_roles WHERE user_id=?", (admin_id,))
            conn.execute("DELETE FROM admins WHERE id=?", (admin_id,))
            return True

    @staticmethod
    def get_user_roles(admin_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT role_id FROM user_roles WHERE user_id=?", (admin_id,)
            ).fetchall()
            return [r["role_id"] for r in rows]

    @staticmethod
    def assign_roles(admin_id: int, role_ids: list):
        with get_connection() as conn:
            conn.execute("DELETE FROM user_roles WHERE user_id=?", (admin_id,))
            for rid in role_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?,?)",
                    (admin_id, rid)
                )
