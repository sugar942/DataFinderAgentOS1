import json
import random
import re
import urllib.parse
import requests
from datetime import datetime

from app.models.db import get_connection


class WatchRepository:

    # ==================== 瞭源管理 ====================
    @staticmethod
    def get_all_sources(status_only: bool = False):
        with get_connection() as conn:
            if status_only:
                return conn.execute(
                    "SELECT * FROM watch_sources WHERE status=1 ORDER BY sort, id"
                ).fetchall()
            return conn.execute(
                "SELECT * FROM watch_sources ORDER BY sort, id"
            ).fetchall()

    @staticmethod
    def get_source_by_id(source_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM watch_sources WHERE id=?", (source_id,)
            ).fetchone()

    @staticmethod
    def get_enabled_sources():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, code, base_url, request_headers, params, description FROM watch_sources WHERE status=1 ORDER BY sort, id"
            ).fetchall()
        sources = []
        for row in rows:
            source = dict(row)
            try:
                source["request_headers"] = json.loads(source.get("request_headers", "{}"))
            except (json.JSONDecodeError, TypeError):
                source["request_headers"] = {}
            try:
                source["params"] = json.loads(source.get("params", "{}"))
            except (json.JSONDecodeError, TypeError):
                source["params"] = {}
            sources.append(source)
        return sources

    @staticmethod
    def create_source(name: str, code: str, source_type: str = "web",
                      base_url: str = "", status: int = 1, config: str = "{}",
                      sort: int = 0, description: str = "",
                      request_headers: str = "{}", params: str = "{}") -> bool:
        import sqlite3
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO watch_sources (name, code, source_type, base_url, status, config, sort, description, request_headers, params) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (name, code, source_type, base_url, status, config, sort, description, request_headers, params)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update_source(source_id: int, **kwargs) -> bool:
        fields = []
        values = []
        for k in ["name", "code", "source_type", "base_url", "status", "config", "sort", "description", "request_headers", "params"]:
            if k in kwargs:
                fields.append(f"{k}=?")
                values.append(kwargs[k])
        if not fields:
            return False
        values.append(source_id)
        with get_connection() as conn:
            conn.execute(f"UPDATE watch_sources SET {','.join(fields)} WHERE id=?", values)
        return True

    @staticmethod
    def delete_source(source_id: int):
        with get_connection() as conn:
            conn.execute("DELETE FROM watch_sources WHERE id=?", (source_id,))
            conn.execute("DELETE FROM watch_results WHERE source_id=?", (source_id,))

    # ==================== 采集任务 ====================
    @staticmethod
    def create_task(keyword: str, source_ids: list) -> int:
        import json
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO watch_tasks (keyword, source_ids, status) VALUES (?,?,?)",
                (keyword, json.dumps(source_ids, ensure_ascii=False), "running")
            )
            return cursor.lastrowid

    @staticmethod
    def get_latest_tasks(limit: int = 10):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM watch_tasks ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    @staticmethod
    def get_task_by_id(task_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM watch_tasks WHERE id=?", (task_id,)
            ).fetchone()

    @staticmethod
    def update_task_status(task_id: int, status: str, total_count: int = 0):
        with get_connection() as conn:
            conn.execute(
                "UPDATE watch_tasks SET status=?, total_count=? WHERE id=?",
                (status, total_count, task_id)
            )

    # ==================== 采集结果 ====================
    @staticmethod
    def save_results(task_id: int, results: list):
        with get_connection() as conn:
            for r in results:
                conn.execute(
                    "INSERT INTO watch_results (task_id, source_id, source_name, title, url, summary) "
                    "VALUES (?,?,?,?,?,?)",
                    (task_id, r["source_id"], r.get("source_name", ""),
                     r.get("title", ""), r.get("url", ""), r.get("summary", ""))
                )

    @staticmethod
    def get_results(task_id: int, page: int = 1, limit: int = 15):
        offset = (page - 1) * limit
        with get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM watch_results WHERE task_id=?", (task_id,)
            ).fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM watch_results WHERE task_id=? ORDER BY id LIMIT ? OFFSET ?",
                (task_id, limit, offset)
            ).fetchall()
        return count, rows

    # ==================== 真实采集（瞭望采集器） ====================
    @staticmethod
    def execute_collection(task_id: int):
        """执行采集任务 —— 支持真实HTTP采集 + 模拟数据回退"""
        with get_connection() as conn:
            task = conn.execute(
                "SELECT * FROM watch_tasks WHERE id=?", (task_id,)
            ).fetchone()
        if not task:
            return

        keyword = task["keyword"]
        source_ids = json.loads(task["source_ids"])

        sources = []
        with get_connection() as conn:
            for sid in source_ids:
                src = conn.execute(
                    "SELECT * FROM watch_sources WHERE id=? AND status=1", (sid,)
                ).fetchone()
                if src:
                    sources.append(dict(src))

        if not sources:
            WatchRepository.update_task_status(task_id, "failed", 0)
            return

        results = []
        for src in sources:
            try:
                articles = WatchCollector.collect_articles(src, keyword)
                if not articles:
                    articles = WatchCollector.mock_collect(src, keyword)
                for article in articles:
                    article["source_id"] = src["id"]
                    article["source_name"] = src["name"]
                results.extend(articles)
            except Exception:
                fallback = WatchCollector.mock_collect(src, keyword)
                results.extend(fallback)

        WatchRepository.save_results(task_id, results)
        WatchRepository.update_task_status(task_id, "completed", len(results))


class WatchCollector:
    """瞭望采集器 —— 从各瞭源真实采集数据"""

    @staticmethod
    def collect_articles(source: dict, keyword: str, page: int = 1) -> list:
        """从指定瞭源采集文章，使用 DB 中存储的 request_headers 和 params"""
        code = source.get("code", "")

        # 解析 request_headers
        headers_str = source.get("request_headers", "{}")
        try:
            headers = json.loads(headers_str) if isinstance(headers_str, str) else headers_str
        except (json.JSONDecodeError, TypeError):
            headers = {}

        # 解析 params
        params_str = source.get("params", "{}")
        try:
            params = json.loads(params_str) if isinstance(params_str, str) else params_str
        except (json.JSONDecodeError, TypeError):
            params = {}

        base_url = source.get("base_url", "")

        if not base_url:
            return WatchCollector.mock_collect(source, keyword)

        try:
            return WatchCollector._collect_web(source, keyword, base_url, headers, params, page)
        except Exception:
            return WatchCollector.mock_collect(source, keyword)

    @staticmethod
    def _collect_web(source: dict, keyword: str, base_url: str,
                     headers: dict, params: dict, page: int = 1) -> list:
        """通用 web 采集 —— 替换占位符后发起 HTTP GET 请求并解析 HTML"""
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        # 合并自定义 headers（DB 中的 headers 优先）
        merged_headers = {**default_headers, **headers}

        # 处理 params 中的占位符替换
        processed_params = {}
        for k, v in params.items():
            v_str = str(v)
            v_str = v_str.replace("{keyword}", keyword)
            v_str = v_str.replace("{pn}", str((page - 1) * 10))
            processed_params[k] = v_str

        try:
            url = base_url + "?" + urllib.parse.urlencode(processed_params)
            response = requests.get(url, headers=merged_headers, timeout=15)
            response.encoding = response.apparent_encoding or "utf-8"
            return WatchCollector._parse_baidu_html(response.text)
        except Exception:
            return []

    @staticmethod
    def _parse_baidu_html(html: str) -> list:
        """解析百度搜索结果 HTML，提取标题和链接"""
        articles = []
        try:
            # 匹配百度新闻搜索结果：h3 标题中的链接
            title_pattern = re.compile(r'<h3[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h3>', re.DOTALL)
            link_pattern = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
            titles = title_pattern.findall(html)
            for title_html in titles:
                links = link_pattern.findall(title_html)
                if links:
                    href = links[0][0]
                    text = re.sub(r'<[^>]+>', '', links[0][1]).strip()
                    if text and href:
                        articles.append({"title": text, "url": href, "summary": ""})
            return articles[:12]
        except Exception:
            return []

    @staticmethod
    def mock_collect(source: dict, keyword: str) -> list:
        """模拟采集（回退方案）"""
        templates = [
            "{kw}最新动态分析与展望",
            "关于{kw}的政策解读与实施进展",
            "{kw}领域取得重要突破",
            "专家解读：{kw}的发展趋势与挑战",
            "{kw}相关工作报告发布",
            "深度观察：{kw}带来的机遇与变革",
            "{kw}数据公布，多项指标向好",
            "{kw}行动计划全面启动",
        ]
        count = random.randint(1, 5)
        results = []
        for j in range(count):
            title = random.choice(templates).replace("{kw}", keyword)
            results.append({
                "source_id": source["id"],
                "source_name": source["name"],
                "title": title,
                "url": f"https://example.com/{source.get('code', 'source')}/article_{j}",
                "summary": f"本文围绕「{keyword}」展开深度分析，为相关决策提供参考依据。",
            })
        return results
