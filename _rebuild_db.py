"""Rebuild db.py with all tables plus conversations"""
import os

# The complete new content for db.py
new_content = '''"""
db.py -- SQLite database access infrastructure
- Uses Python3 built-in sqlite3 module, no third-party deps
- Centralized DB path, connection creation, row_factory config
- Auto-creates tables and seed admin account on first run
"""
import json
import os
import sqlite3

def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir))

DB_PATH = os.path.join(project_root(),"database","finderos.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH),exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admins(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                is_super BOOLEAN NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS roles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                status INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS functions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                url TEXT DEFAULT '',
                method TEXT DEFAULT 'GET',
                parent_id INTEGER NOT NULL DEFAULT 0,
                type TEXT NOT NULL DEFAULT 'menu',
                sort INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS menus(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                icon TEXT DEFAULT '',
                url TEXT DEFAULT '',
                parent_id INTEGER NOT NULL DEFAULT 0,
                sort INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS role_functions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                function_id INTEGER NOT NULL,
                UNIQUE(role_id, function_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS role_menus(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                menu_id INTEGER NOT NULL,
                UNIQUE(role_id, menu_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_roles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                UNIQUE(user_id, role_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS operation_logs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                user_type TEXT NOT NULL DEFAULT 'user',
                action TEXT NOT NULL,
                detail TEXT DEFAULT '',
                ip_address TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watch_sources(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                source_type TEXT NOT NULL DEFAULT 'web',
                base_url TEXT DEFAULT '',
                status INTEGER NOT NULL DEFAULT 1,
                config TEXT DEFAULT '{}',
                sort INTEGER NOT NULL DEFAULT 0,
                description TEXT DEFAULT '',
                request_headers TEXT DEFAULT '{}',
                params TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watch_tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                source_ids TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                total_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watch_results(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                source_id INTEGER NOT NULL,
                source_name TEXT DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                url TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                published_at TEXT DEFAULT '',
                collected_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_models(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                model_id TEXT NOT NULL,
                api_key TEXT NOT NULL,
                base_url TEXT NOT NULL,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 4096,
                top_p REAL DEFAULT 0.9,
                frequency_penalty REAL DEFAULT 0.0,
                presence_penalty REAL DEFAULT 0.0,
                is_default INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1,
                total_tokens INTEGER DEFAULT 0,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                description TEXT,
                provider TEXT DEFAULT 'openai',
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS digital_employees(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL DEFAULT 'llm',
                model_id INTEGER DEFAULT 0,
                prompt TEXT DEFAULT '',
                skill_config TEXT DEFAULT '{}',
                enable_crawl4ai INTEGER NOT NULL DEFAULT 0,
                api_url TEXT DEFAULT '',
                api_method TEXT DEFAULT 'GET',
                api_params TEXT DEFAULT '{}',
                api_headers TEXT DEFAULT '{}',
                api_body TEXT DEFAULT '{}',
                response_type TEXT DEFAULT 'json',
                icon TEXT DEFAULT 'fas fa-robot',
                description TEXT DEFAULT '',
                status INTEGER NOT NULL DEFAULT 1,
                sort INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_warehouse(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                content TEXT,
                url TEXT,
                source TEXT,
                source_id INTEGER DEFAULT 0,
                keyword TEXT,
                image_url TEXT,
                is_deep_collected INTEGER NOT NULL DEFAULT 0,
                deep_collect_time TEXT,
                status INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deep_collect_tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL DEFAULT 0,
                employee_name TEXT DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                title TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                progress INTEGER NOT NULL DEFAULT 0,
                step TEXT DEFAULT '',
                logs TEXT DEFAULT '[]',
                result_id INTEGER DEFAULT 0,
                error TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deep_collect_results(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                title TEXT DEFAULT '',
                content TEXT DEFAULT '',
                html TEXT DEFAULT '',
                markdown TEXT DEFAULT '',
                url TEXT DEFAULT '',
                word_count INTEGER DEFAULT 0,
                image_urls TEXT DEFAULT '[]',
                collected_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT '新对话',
                model_name TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
                content TEXT NOT NULL DEFAULT '',
                tokens INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON chat_messages(conversation_id)")

        cursor = conn.execute("SELECT COUNT(*) FROM roles WHERE code='super_admin'")
        if cursor.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO roles (name, code, description, status) VALUES (?,?,?,?)",
                ("超级管理员", "super_admin", "系统内置超级管理员角色，拥有所有权限", 1)
            )

        cursor = conn.execute("SELECT COUNT(*) FROM menus")
        if cursor.fetchone()[0] == 0:
            default_menus = [
                (1, "系统首页", "fas fa-tachometer-alt", "/admin/index", 0, 0, 1),
                (2, "用户权限", "fas fa-users-cog", "", 0, 1, 1),
                (3, "用户列表", "", "/admin/users", 2, 0, 1),
                (4, "角色管理", "", "/admin/roles", 2, 1, 1),
                (5, "功能管理", "", "/admin/functions", 2, 2, 1),
                (6, "菜单管理", "", "/admin/menus", 2, 3, 1),
                (7, "数据采集", "fas fa-satellite-dish", "", 0, 2, 1),
                (8, "瞭望配置", "", "/admin/watch", 7, 0, 1),
                (9, "数据源管理", "", "/admin/data", 7, 1, 1),
                (10, "采集调度", "", "/admin/collection", 7, 2, 1),
                (11, "AI 引擎", "fas fa-brain", "", 0, 3, 1),
                (12, "智能助手", "", "/admin/digital_employee", 11, 0, 1),
                (13, "模型管理", "", "/admin/model", 11, 1, 1),
                (14, "数智大屏", "fas fa-chart-pie", "/admin/dashboard", 0, 4, 1),
                (15, "舆情分析", "fas fa-comment-dots", "/admin/sentiment", 0, 5, 1),
            ]
            conn.executemany(
                "INSERT INTO menus (id, name, icon, url, parent_id, sort, status) VALUES (?,?,?,?,?,?,?)",
                default_menus
            )

        cursor = conn.execute("SELECT COUNT(*) FROM functions")
        if cursor.fetchone()[0] == 0:
            default_functions = [
                (1, "系统首页", "dashboard", "/admin/index", "GET", 0, "menu", 0, 1),
                (2, "用户管理", "user", "", "", 0, "menu", 1, 1),
                (3, "用户列表", "user:list", "/admin/api/users", "GET", 2, "api", 0, 1),
                (4, "新增用户", "user:create", "/admin/api/users", "POST", 2, "api", 1, 1),
                (5, "编辑用户", "user:update", "/admin/api/users", "PUT", 2, "api", 2, 1),
                (6, "删除用户", "user:delete", "/admin/api/users", "DELETE", 2, "api", 3, 1),
                (7, "角色管理", "role", "", "", 0, "menu", 2, 1),
                (8, "角色列表", "role:list", "/admin/api/roles", "GET", 7, "api", 0, 1),
                (9, "新增角色", "role:create", "/admin/api/roles", "POST", 7, "api", 1, 1),
                (10, "编辑角色", "role:update", "/admin/api/roles", "PUT", 7, "api", 2, 1),
                (11, "删除角色", "role:delete", "/admin/api/roles", "DELETE", 7, "api", 3, 1),
                (12, "功能管理", "function", "", "", 0, "menu", 3, 1),
                (13, "功能列表", "function:list", "/admin/api/functions", "GET", 12, "api", 0, 1),
                (14, "新增功能", "function:create", "/admin/api/functions", "POST", 12, "api", 1, 1),
                (15, "编辑功能", "function:update", "/admin/api/functions", "PUT", 12, "api", 2, 1),
                (16, "删除功能", "function:delete", "/admin/api/functions", "DELETE", 12, "api", 3, 1),
                (17, "菜单管理", "menu", "", "", 0, "menu", 4, 1),
                (18, "菜单列表", "menu:list", "/admin/api/menus", "GET", 17, "api", 0, 1),
                (19, "新增菜单", "menu:create", "/admin/api/menus", "POST", 17, "api", 1, 1),
                (20, "编辑菜单", "menu:update", "/admin/api/menus", "PUT", 17, "api", 2, 1),
                (21, "删除菜单", "menu:delete", "/admin/api/menus", "DELETE", 17, "api", 3, 1),
            ]
            conn.executemany(
                "INSERT INTO functions (id, name, code, url, method, parent_id, type, sort, status) VALUES (?,?,?,?,?,?,?,?,?)",
                default_functions
            )

        cursor = conn.execute("SELECT COUNT(*) FROM role_functions")
        if cursor.fetchone()[0] == 0:
            for fid in range(1, 22):
                conn.execute(
                    "INSERT OR IGNORE INTO role_functions (role_id, function_id) VALUES (?,?)",
                    (1, fid)
                )

        cursor = conn.execute("SELECT COUNT(*) FROM role_menus")
        if cursor.fetchone()[0] == 0:
            for mid in range(1, 16):
                conn.execute(
                    "INSERT OR IGNORE INTO role_menus (role_id, menu_id) VALUES (?,?)",
                    (1, mid)
                )

        cursor = conn.execute("SELECT COUNT(*) FROM user_roles")
        if cursor.fetchone()[0] == 0:
            conn.execute(
                "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?,?)",
                (1, 1)
            )

        cursor = conn.execute("SELECT COUNT(*) FROM watch_sources")
        if cursor.fetchone()[0] == 0:
            baidu_news_headers = json.dumps({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Cache-Control": "no-cache",
                "Host": "www.baidu.com",
                "sec-ch-ua": "\\"Not)A;Brand\\";v=\\"8\\", \\"Chromium\\";v=\\"138\\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\\"Windows\\"",
            }, ensure_ascii=False)
            baidu_news_params = json.dumps({
                "rtt": "1", "bsst": "1", "cl": "2", "tn": "news",
                "rsv_dl": "ns_pc", "word": "{keyword}", "pn": "{pn}"
            }, ensure_ascii=False)

            default_sources = [
                ("百度新闻搜索", "baidu_news", "web", "https://www.baidu.com/s", 1,
                 '{"page_size":10,"type":"news"}', 0,
                 "百度新闻搜索频道，支持关键词+分页采集，使用完整RequestHeaders模拟浏览器请求",
                 baidu_news_headers, baidu_news_params),
                ("必应新闻搜索", "bing_news", "web", "https://www.bing.com/news/search", 1,
                 '{"page_size":10,"type":"news"}', 1,
                 "必应新闻搜索频道", "{}",
                 '{"q":"{keyword}","first":"{pn}","format":"RSS"}'),
                ("搜狗微信搜索", "sogou_wechat", "web", "https://weixin.sogou.com/weixin", 1,
                 '{"page_size":10,"type":"wechat"}', 2,
                 "搜狗微信搜索频道", "{}",
                 '{"type":"2","query":"{keyword}","page":"{pn}"}'),
                ("360资讯搜索", "360_news", "web", "https://news.so.com/ns", 1,
                 '{"page_size":10,"type":"news"}', 3,
                 "360搜索资讯频道", "{}",
                 '{"q":"{keyword}","pn":"{pn}","src":"news"}'),
                ("微博搜索", "weibo_search", "web", "https://s.weibo.com/weibo", 1,
                 '{"page_size":20,"type":"social"}', 4,
                 "微博搜索频道", "{}",
                 '{"q":"{keyword}","page":"{pn}"}'),
                ("知乎搜索", "zhihu_search", "web", "https://www.zhihu.com/search", 1,
                 '{"page_size":10,"type":"qa"}', 5,
                 "知乎搜索频道", "{}",
                 '{"q":"{keyword}","offset":"{pn}","type":"content"}'),
                ("人民网搜索", "people_search", "web", "http://search.people.com.cn/search", 1,
                 '{"page_size":10,"type":"official"}', 6,
                 "人民网搜索频道（官方媒体）", "{}",
                 '{"keyword":"{keyword}","pageNo":"{pn}"}'),
                ("新华网搜索", "xinhua_search", "web", "http://search.news.cn/search", 1,
                 '{"page_size":10,"type":"official"}', 7,
                 "新华网搜索频道（官方媒体）", "{}",
                 '{"keyword":"{keyword}","page":"{pn}"}'),
            ]
            conn.executemany(
                "INSERT INTO watch_sources (name, code, source_type, base_url, status, config, sort, description, request_headers, params) VALUES (?,?,?,?,?,?,?,?,?,?)",
                default_sources
            )

        cursor = conn.execute("SELECT COUNT(*) FROM admins WHERE username='root'")
        count = cursor.fetchone()[0]
        if count == 0:
            import hashlib
            import secrets
            salt = secrets.token_bytes(16)
            password_hash = hashlib.pbkdf2_hmac("sha256", "libSys2025!".encode("utf-8"), salt, 100_000).hex()
            conn.execute(
                "INSERT INTO admins (username, password_hash, salt, is_super) VALUES (?,?,?,?)",
                ("root", password_hash, salt.hex(), 1)
            )
'''

db_path = os.path.join(os.path.dirname(__file__) or '.', 'app', 'models', 'db.py')
with open(db_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print('db.py rebuilt successfully')
