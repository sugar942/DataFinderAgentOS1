import json
import sqlite3
import requests
import urllib.parse

from app.models.db import get_connection


class DigitalEmployeeRepository:

    @staticmethod
    def get_all(page=1, page_size=10, keyword=""):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            if keyword:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM digital_employees WHERE name LIKE ? OR code LIKE ? OR description LIKE ?",
                    (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")
                )
                total = cursor.fetchone()[0]
                cursor = conn.execute(
                    """SELECT * FROM digital_employees
                    WHERE name LIKE ? OR code LIKE ? OR description LIKE ?
                    ORDER BY sort ASC, created_at DESC LIMIT ? OFFSET ?""",
                    (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", page_size, offset)
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM digital_employees")
                total = cursor.fetchone()[0]
                cursor = conn.execute(
                    "SELECT * FROM digital_employees ORDER BY sort ASC, created_at DESC LIMIT ? OFFSET ?",
                    (page_size, offset)
                )
            rows = cursor.fetchall()
        return [dict(row) for row in rows], total

    @staticmethod
    def get_by_id(emp_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM digital_employees WHERE id=?", (emp_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_code(code):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM digital_employees WHERE code=?", (code,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(name, code, emp_type="llm", model_id=0, prompt="",
               skill_config="{}", enable_crawl4ai=0, api_url="",
               api_method="GET", api_params="{}", api_headers="{}",
               api_body="{}", response_type="json", icon="fas fa-robot",
               description="", status=1, sort=0):
        try:
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO digital_employees
                    (name, code, type, model_id, prompt, skill_config, enable_crawl4ai,
                     api_url, api_method, api_params, api_headers, api_body,
                     response_type, icon, description, status, sort)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (name, code, emp_type, model_id, prompt, skill_config,
                     enable_crawl4ai, api_url, api_method, api_params,
                     api_headers, api_body, response_type, icon, description,
                     status, sort)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(emp_id, **kwargs):
        if not kwargs:
            return False
        fields = []
        params = []
        for k in ["name", "code", "type", "model_id", "prompt", "skill_config",
                   "enable_crawl4ai", "api_url", "api_method", "api_params",
                   "api_headers", "api_body", "response_type", "icon",
                   "description", "status", "sort"]:
            if k in kwargs:
                fields.append(f"{k}=?")
                params.append(kwargs[k])
        if not fields:
            return False
        fields.append("updated_at=datetime('now','localtime')")
        params.append(emp_id)
        try:
            with get_connection() as conn:
                conn.execute(
                    f"UPDATE digital_employees SET {', '.join(fields)} WHERE id=?",
                    params
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(emp_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM digital_employees WHERE id=?", (emp_id,))
        return True

    @staticmethod
    def get_active():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM digital_employees WHERE status=1 ORDER BY sort ASC, created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]


class DigitalEmployeeService:

    @staticmethod
    def _parse_baidu_news_html(html_text):
        import re
        articles = []

        # Strategy 1: Match <a> tags with href to external sites (news articles)
        # Modern Baidu wraps results in complex JS-rendered structures,
        # but href links to external news sites are still present in the HTML
        link_pattern = re.compile(
            r'<a[^>]*href=\"(https?://(?!www\.baidu\.com|baidu\.com|javascript)[^\"]+)\"[^>]*>(.*?)</a>',
            re.DOTALL
        )
        seen_urls = set()
        for url, text in link_pattern.findall(html_text):
            url = url.strip()
            title = re.sub(r'<[^>]+>', '', text).strip()
            title = re.sub(r'\s+', ' ', title)
            if len(title) > 6 and url not in seen_urls and len(title) < 300:
                seen_urls.add(url)
                articles.append({"title": title, "url": url, "summary": ""})
            if len(articles) >= 20:
                break

        # Strategy 2: Look for embedded JSON data (common in modern SSR pages)
        if not articles:
            json_matches = re.findall(
                r'\"title\"\s*:\s*\"([^\"]+)\".*?\"url\"\s*:\s*\"(https?://[^\"]+)\"',
                html_text[:200000]
            )
            for title, url in json_matches[:20]:
                if len(title) > 6 and url not in seen_urls:
                    seen_urls.add(url)
                    articles.append({"title": title, "url": url, "summary": ""})

        # Strategy 3: Fallback - any reasonable-looking text links
        if not articles:
            text_links = re.findall(
                r'<a[^>]*href=\"(https?://[^\"]+)\"[^>]*>([^<]{6,200})</a>',
                html_text[:200000]
            )
            for url, text in text_links[:20]:
                if 'baidu.com' not in url and url not in seen_urls:
                    title = text.strip()
                    articles.append({"title": title, "url": url, "summary": ""})

        return articles

    @staticmethod
    def execute_llm_employee(employee, user_message, context=None):
        from app.models.model import AIModelRepository, AIModelService

        model = None
        if employee.get("model_id") and employee["model_id"] > 0:
            model = AIModelRepository.get_model_by_id(employee["model_id"])
        if not model:
            model = AIModelRepository.get_default_model()
        if not model:
            return {"success": False, "error": "未找到可用的AI模型"}

        system_prompt = employee.get("prompt", "你是一个智能助手，请根据用户指令完成任务。")
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "system", "content": f"上下文信息:\n{json.dumps(context, ensure_ascii=False)}"})
        messages.append({"role": "user", "content": user_message})

        skill_config = {}
        try:
            raw = employee.get("skill_config", "{}")
            skill_config = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            pass

        try:
            result = AIModelService.chat_completion_sync(model, messages)
            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"]["content"]
                return {"success": True, "content": content, "type": "text"}
            return {"success": False, "error": "模型无响应"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def execute_api_employee(employee, params=None):
        url = employee.get("api_url", "")
        method = employee.get("api_method", "GET").upper()
        api_params_str = employee.get("api_params", "{}")
        api_headers_str = employee.get("api_headers", "{}")
        api_body_str = employee.get("api_body", "{}")

        try:
            api_params = json.loads(api_params_str) if isinstance(api_params_str, str) else api_params_str
        except (json.JSONDecodeError, TypeError):
            api_params = {}
        try:
            api_headers = json.loads(api_headers_str) if isinstance(api_headers_str, str) else api_headers_str
        except (json.JSONDecodeError, TypeError):
            api_headers = {}
        try:
            api_body = json.loads(api_body_str) if isinstance(api_body_str, str) else api_body_str
        except (json.JSONDecodeError, TypeError):
            api_body = {}

        if params:
            for k, v in params.items():
                placeholder = "{" + k + "}"
                # Replace in URL
                url = url.replace(placeholder, str(v))
                # Replace in all param values
                for pk, pv in api_params.items():
                    if isinstance(pv, str) and placeholder in pv:
                        api_params[pk] = pv.replace(placeholder, str(v))
                # Replace in body
                if isinstance(api_body, str):
                    api_body = api_body.replace(placeholder, str(v))
                # Also set the param directly
                api_params[k] = str(v)

        try:
            if method == "GET":
                resp = requests.get(url, params=api_params, headers=api_headers, timeout=30)
            elif method == "POST":
                resp = requests.post(url, params=api_params, headers=api_headers, json=api_body, timeout=30)
            elif method == "PUT":
                resp = requests.put(url, params=api_params, headers=api_headers, json=api_body, timeout=30)
            elif method == "DELETE":
                resp = requests.delete(url, params=api_params, headers=api_headers, timeout=30)
            else:
                return {"success": False, "error": f"不支持的请求方法: {method}"}

            response_type = employee.get("response_type", "json")
            if response_type == "json":
                try:
                    return {"success": True, "content": resp.json(), "type": "json",
                            "status_code": resp.status_code}
                except ValueError:
                    return {"success": True, "content": resp.text, "type": "text",
                            "status_code": resp.status_code}

            # For text/html responses from Baidu, parse articles
            content_type = resp.headers.get("Content-Type", "")
            if "baidu.com" in url and ("text/html" in content_type or resp.text.strip().startswith("<!DOCTYPE")):
                articles = DigitalEmployeeService._parse_baidu_news_html(resp.text)
                if articles:
                    return {"success": True, "content": articles, "type": "articles",
                            "status_code": resp.status_code, "count": len(articles)}

            return {"success": True, "content": resp.text, "type": "text",
                    "status_code": resp.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def execute(employee, user_message=None, params=None, context=None):
        if employee.get("type") == "api":
            return DigitalEmployeeService.execute_api_employee(employee, params or {})
        return DigitalEmployeeService.execute_llm_employee(employee, user_message or "", context)
