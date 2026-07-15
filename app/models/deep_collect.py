import json
import threading
import traceback

from app.models.db import get_connection


class DeepCollectRepository:

    @staticmethod
    def create_task(warehouse_id, url, title="", employee_id=0, employee_name=""):
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO deep_collect_tasks
                (warehouse_id, employee_id, employee_name, url, title, status, progress, step, logs)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (warehouse_id, employee_id, employee_name, url, title,
                 "pending", 0, "任务已创建", "[]")
            )
            return cursor.lastrowid

    @staticmethod
    def get_task(task_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM deep_collect_tasks WHERE id=?", (task_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_tasks_by_warehouse(warehouse_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM deep_collect_tasks WHERE warehouse_id=? ORDER BY id DESC",
                (warehouse_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_all_tasks(page=1, page_size=20):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM deep_collect_tasks")
            total = cursor.fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM deep_collect_tasks ORDER BY id DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
        return [dict(r) for r in rows], total

    @staticmethod
    def update_task(task_id, **kwargs):
        import time
        fields = []
        params = []
        for k, v in kwargs.items():
            fields.append(f"{k}=?")
            if isinstance(v, (list, dict)):
                params.append(json.dumps(v, ensure_ascii=False))
            else:
                params.append(v)
        fields.append("updated_at=datetime('now','localtime')")
        params.append(task_id)
        for attempt in range(3):
            try:
                with get_connection() as conn:
                    conn.execute(
                        f"UPDATE deep_collect_tasks SET {', '.join(fields)} WHERE id=?",
                        params
                    )
                return
            except Exception:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    raise

    @staticmethod
    def append_log(task_id, message):
        task = DeepCollectRepository.get_task(task_id)
        if not task:
            return
        try:
            logs = json.loads(task.get("logs", "[]"))
        except (json.JSONDecodeError, TypeError):
            logs = []
        logs.append(message)
        DeepCollectRepository.update_task(task_id, logs=logs)

    @staticmethod
    def save_result(task_id, warehouse_id, title="", content="", html="",
                    markdown="", url="", word_count=0, image_urls=None):
        if image_urls is None:
            image_urls = []
        result_id = None
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO deep_collect_results
                (task_id, warehouse_id, title, content, html, markdown, url, word_count, image_urls)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (task_id, warehouse_id, title, content, html, markdown, url,
                 word_count, json.dumps(image_urls, ensure_ascii=False))
            )
            result_id = cursor.lastrowid
        if result_id:
            DeepCollectRepository.update_task(task_id, result_id=result_id)
        return result_id

    @staticmethod
    def get_result_by_task(task_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM deep_collect_results WHERE task_id=? ORDER BY id DESC LIMIT 1",
                (task_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_result_by_warehouse(warehouse_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM deep_collect_results WHERE warehouse_id=? ORDER BY id DESC LIMIT 1",
                (warehouse_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def delete_task(task_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM deep_collect_results WHERE task_id=?", (task_id,))
            conn.execute("DELETE FROM deep_collect_tasks WHERE id=?", (task_id,))


class DeepCollectService:

    @staticmethod
    def _get_collector_employee():
        """查找采集专员数字员工"""
        from app.models.digital_employee import DigitalEmployeeRepository
        emp = DigitalEmployeeRepository.get_by_code("collector")
        if emp and emp.get("status") == 1 and emp.get("enable_crawl4ai") == 1:
            return emp
        # Fallback: find any active employee with crawl4ai enabled
        employees = DigitalEmployeeRepository.get_active()
        for emp in employees:
            if emp.get("enable_crawl4ai") == 1:
                return emp
        return None

    @staticmethod
    def run_deep_collect(task_id):
        """在线程中执行深度采集，通过 crawl4ai 采集网页完整内容"""
        import asyncio

        task = DeepCollectRepository.get_task(task_id)
        if not task:
            return

        url = task.get("url", "")
        if not url:
            DeepCollectRepository.update_task(
                task_id, status="failed", step="无采集URL", error="未提供URL", progress=0
            )
            return

        # Look up collector digital employee
        employee = DeepCollectService._get_collector_employee()
        if not employee:
            DeepCollectRepository.update_task(
                task_id, status="failed", step="无可用采集专员",
                error="未找到启用crawl4ai的数字员工，请先在数字员工管理中配置采集专员并启用crawl4ai", progress=0
            )
            DeepCollectRepository.append_log(task_id, "[ERROR] 未找到可用的采集专员数字员工")
            return

        try:
            DeepCollectRepository.update_task(
                task_id, status="running", step="正在初始化浏览器...", progress=5,
                employee_id=employee["id"], employee_name=employee["name"]
            )
            DeepCollectRepository.append_log(task_id, "[INFO] 开始深度采集任务")
            DeepCollectRepository.append_log(task_id, f"[INFO] 调度数字员工: {employee['name']}")
            DeepCollectRepository.append_log(task_id, f"[INFO] 目标URL: {url}")

            # Run async crawl4ai in sync context
            result = asyncio.run(DeepCollectService._crawl_url(url, task_id))

            if result.get("success"):
                DeepCollectRepository.save_result(
                    task_id=task_id,
                    warehouse_id=task["warehouse_id"],
                    title=result.get("title", task.get("title", "")),
                    content=result.get("content", ""),
                    html=result.get("html", ""),
                    markdown=result.get("markdown", ""),
                    url=url,
                    word_count=result.get("word_count", 0),
                    image_urls=result.get("image_urls", []),
                )
                DeepCollectRepository.update_task(
                    task_id, status="completed", progress=100,
                    step="采集完成"
                )
                DeepCollectRepository.append_log(task_id, f"[SUCCESS] 采集完成，共 {result.get('word_count', 0)} 字")

                # Mark warehouse record as deep collected
                from app.models.warehouse import DataWarehouseRepository
                DataWarehouseRepository.mark_deep_collected(task["warehouse_id"])
                DataWarehouseRepository.update_record(
                    task["warehouse_id"],
                    content=result.get("content", "")[:10000]
                )
            else:
                DeepCollectRepository.update_task(
                    task_id, status="failed", progress=0,
                    step="采集失败", error=result.get("error", "未知错误")
                )
                DeepCollectRepository.append_log(task_id, f"[ERROR] {result.get('error', '未知错误')}")

        except Exception as e:
            DeepCollectRepository.update_task(
                task_id, status="failed", progress=0,
                step="采集异常", error=str(e)
            )
            DeepCollectRepository.append_log(task_id, f"[ERROR] 异常: {str(e)}")
            DeepCollectRepository.append_log(task_id, traceback.format_exc())

    @staticmethod
    async def _crawl_url(url, task_id):
        """使用 crawl4ai 采集网页"""
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

        DeepCollectRepository.update_task(task_id, progress=10, step="正在启动浏览器...")
        DeepCollectRepository.append_log(task_id, "[INFO] 启动 headless 浏览器...")

        try:
            browser_config = BrowserConfig(
                headless=True,
                verbose=False,
                text_mode=False,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            crawl_config = CrawlerRunConfig(
                page_timeout=60000,
                wait_until="domcontentloaded",
                word_count_threshold=1,
                only_text=False,
            )

            DeepCollectRepository.update_task(task_id, progress=30, step="正在加载页面...")
            DeepCollectRepository.append_log(task_id, "[INFO] 正在加载目标页面...")

            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=crawl_config)

                DeepCollectRepository.update_task(task_id, progress=60, step="正在提取内容...")
                DeepCollectRepository.append_log(task_id, "[INFO] 页面加载完成，正在提取内容...")

                html_content = result.html or ""
                markdown_content = result.markdown or ""
                title = ""
                if hasattr(result, 'title'):
                    title = result.title or ""
                elif hasattr(result, 'metadata') and result.metadata:
                    title = result.metadata.get('title', '')

                # Extract plain text content
                content = markdown_content
                if not content:
                    import re
                    content = re.sub(r'<[^>]+>', '', html_content)
                    content = re.sub(r'\s+', ' ', content)

                image_urls = []
                if hasattr(result, 'media') and result.media:
                    image_urls = result.media.get('images', [])

                word_count = len(content)

                DeepCollectRepository.append_log(task_id, f"[INFO] 标题: {title or '未提取到'}")
                DeepCollectRepository.append_log(task_id, f"[INFO] 内容长度: {word_count} 字符")

                return {
                    "success": True,
                    "title": title,
                    "content": content,
                    "html": html_content,
                    "markdown": markdown_content,
                    "word_count": word_count,
                    "image_urls": image_urls,
                }

        except Exception as e:
            DeepCollectRepository.append_log(task_id, f"[ERROR] crawl4ai采集异常: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def start_async(task_id):
        t = threading.Thread(target=DeepCollectService.run_deep_collect, args=(task_id,), daemon=True)
        t.start()
        return t
