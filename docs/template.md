# DataFinderAgentOS 代码模板与规范

## 1. Controller 模板

### 1.1 基础 Handler

```python
import tornado.web
from app.controllers.base import BaseHandler

class ExampleHandler(BaseHandler):
    def get(self):
        self.render("example.html", title="页面标题")

    def post(self):
        pass
```

### 1.2 需要认证的 Handler

```python
import tornado.web
from app.controllers.base import BaseHandler

class SecuredHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = self.current_user
        self.render("secured.html", title="安全页面", username=username)
```

### 1.3 命名规范

| 类型 | 示例 | 说明 |
|------|------|------|
| 登录 | LoginHandler | 处理登录 |
| 登出 | LogoutHandler | 处理登出 |
| 首页 | IndexHandler | 首页展示 |
| 列表 | ListHandler | 列表展示 |
| 详情 | DetailHandler | 详情展示 |
| WebSocket | ChatWebSocketHandler | WebSocket 连接 |

### 1.4 WebSocket Handler 模板

```python
import json
import tornado.websocket
from app.controllers.base import BaseHandler

class ChatWebSocketHandler(BaseHandler, tornado.websocket.WebSocketHandler):
    def open(self):
        username = self.get_current_user()
        if not username:
            self.close(code=401, reason="未登录")
            return
        self.username = username

    def on_message(self, message):
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            msg_data = data.get("data")

            if msg_type == "message":
                self.handle_message(msg_data)
            elif msg_type == "ping":
                self.write_message({"type": "pong"})
        except json.JSONDecodeError:
            self.write_message({"type": "error", "data": "消息格式不正确"})

    def handle_message(self, content):
        from app.models.llm_service import LLMService
        llm = LLMService()
        for chunk in llm.chat_stream(self.username, content):
            self.write_message({"type": "stream", "data": chunk})
        self.write_message({"type": "done"})

    def on_close(self):
        pass

    def check_origin(self, origin):
        return True
```

### 1.5 大模型服务模板

```python
import os
import openai

class LLMService:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    def chat_stream(self, username: str, content: str):
        messages = [
            {"role": "system", "content": "你是一个数据分析助手"},
            {"role": "user", "content": content}
        ]

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def chat(self, username: str, content: str) -> str:
        messages = [
            {"role": "system", "content": "你是一个数据分析助手"},
            {"role": "user", "content": content}
        ]

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False
        )

        return resp.choices[0].message.content
```

### 1.6 智能助手服务模板

```python
import re

class DigitalEmployeeService:
    def __init__(self):
        self.cmd_map = {
            "@天气": self.do_weather,
            "@新闻": self.do_news,
            "@音乐": self.do_music,
            "@电影": self.do_movie,
            "@川哥": self.do_chuange
        }

    def parse(self, content: str):
        for cmd, fn in self.cmd_map.items():
            if content.startswith(cmd):
                args = content[len(cmd):].strip()
                return fn, args
        return None, content

    def do_weather(self, args: str):
        city = args if args else "北京"
        return f"正在查询 {city} 的天气..."

    def do_news(self, args: str):
        kw = args if args else ""
        return f"正在获取{'关键词"' + kw + '"的' if kw else ''}新闻资讯..."

    def do_music(self, args: str):
        song = args if args else ""
        return f"正在搜索{'歌曲"' + song + '"' if song else '音乐'}..."

    def do_movie(self, args: str):
        movie = args if args else ""
        return f"正在查询{'电影"' + movie + '"' if movie else '电影'}信息..."

    def do_chuange(self, args: str):
        return "川哥说：你好！有什么需要帮忙的吗？"
```

## 2. Model 模板

### 2.1 Repository 类

```python
import sqlite3
from app.models.db import get_connection

class ExampleRepository:
    @staticmethod
    def create(data: dict) -> bool:
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO table_name (col1, col2) VALUES (?, ?)",
                    (data["col1"], data["col2"])
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def find_by_id(id: int):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM table_name WHERE id=?",
                (id,)
            ).fetchone()
        return row

    @staticmethod
    def find_all():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM table_name").fetchall()
        return rows

    @staticmethod
    def update(id: int, data: dict) -> bool:
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE table_name SET col1=?, col2=? WHERE id=?",
                    (data["col1"], data["col2"], id)
                )
            return True
        except sqlite3.Error:
            return False

    @staticmethod
    def remove(id: int) -> bool:
        try:
            with get_connection() as conn:
                conn.execute("DELETE FROM table_name WHERE id=?", (id,))
            return True
        except sqlite3.Error:
            return False
```

### 2.2 建表模板

在 `app/models/db.py` 的 `init_db()` 中添加：

```python
conn.execute("""
    CREATE TABLE IF NOT EXISTS example_table(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        column1 TEXT NOT NULL,
        column2 INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    )
""")
```

## 3. 模板引擎

### 3.1 前台基础模板 (base.html)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <meta name="theme-color" content="#1a1a2e">
    <title>{{ title }}</title>
    <link rel="stylesheet" type="text/css" href="{{ static_url('dist/layui/css/layui.css') }}">
    <link rel="stylesheet" type="text/css" href="{{ static_url('dist/bootstrap/css/bootstrap.min.css') }}">
    <link rel="stylesheet" type="text/css" href="{{ static_url('css/base.css') }}">
</head>
<body class="app-body">
    <div class="app-container">
        {% block body %}{% end %}
    </div>
    <script src="{{ static_url('dist/layui/layui.js') }}"></script>
    <script src="{{ static_url('dist/bootstrap/js/bootstrap.bundle.min.js') }}"></script>
    <script src="{{ static_url('js/base.js') }}"></script>
</body>
</html>
```

### 3.2 前台子模板

```html
{% extends "base.html" %}
{% block body %}
<!-- 页面内容 -->
{% end %}
```

### 3.3 后台基础模板 (admin/base.html)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }}</title>
    <link rel="stylesheet" type="text/css" href="{{ static_url('dist/layui/css/layui.css') }}">
    <link rel="stylesheet" type="text/css" href="{{ static_url('css/base.css') }}">
</head>
<body class="layui-layout layui-layout-admin">
    <div class="layui-header">
        <div class="layui-logo">智能瞭望与问数系统</div>
        <ul class="layui-nav layui-layout-right">
            <li class="layui-nav-item"><a href="/admin/logout">退出</a></li>
        </ul>
    </div>
    <div class="layui-side layui-bg-black">
        <div class="layui-side-scroll">
            <ul class="layui-nav layui-nav-tree">
                <li class="layui-nav-item"><a href="/admin/index">首页</a></li>
                <li class="layui-nav-item"><a href="/admin/users">用户管理</a></li>
                <li class="layui-nav-item"><a href="/admin/functions">功能管理</a></li>
                <li class="layui-nav-item"><a href="/admin/menus">菜单管理</a></li>
                <li class="layui-nav-item"><a href="/admin/roles">角色管理</a></li>
                <li class="layui-nav-item"><a href="/admin/watch">瞭望管理</a></li>
                <li class="layui-nav-item"><a href="/admin/data">数据管理</a></li>
                <li class="layui-nav-item"><a href="/admin/collection">采集管理</a></li>
                <li class="layui-nav-item"><a href="/admin/digital_employee">智能助手</a></li>
                <li class="layui-nav-item"><a href="/admin/model">模型引擎</a></li>
                <li class="layui-nav-item"><a href="/admin/dashboard">数智大屏</a></li>
                <li class="layui-nav-item"><a href="/admin/sentiment">舆情大屏</a></li>
            </ul>
        </div>
    </div>
    <div class="layui-body">
        {% block body %}{% end %}
    </div>
    <script src="{{ static_url('dist/layui/layui.js') }}"></script>
</body>
</html>
```

### 3.4 表单模板（含 XSRF）

```html
<form method="post" action="?">
    {% module xsrf_form_html() %}
    <input type="text" name="field">
    <button type="submit">提交</button>
</form>
```

### 3.5 layui 表单模板

```html
<form class="layui-form" method="post" action="?">
    {% module xsrf_form_html() %}
    <div class="layui-form-item">
        <label class="layui-form-label">用户名</label>
        <div class="layui-input-block">
            <input type="text" name="username" lay-verify="required" class="layui-input">
        </div>
    </div>
    <div class="layui-form-item">
        <label class="layui-form-label">密码</label>
        <div class="layui-input-block">
            <input type="password" name="password" lay-verify="required" class="layui-input">
        </div>
    </div>
    <div class="layui-form-item">
        <div class="layui-input-block">
            <button class="layui-btn" lay-submit lay-filter="submit">提交</button>
        </div>
    </div>
</form>
<script>
layui.use(['form'], function(){
    var form = layui.form;
    form.on('submit(submit)', function(data){
        return true;
    });
});
</script>
```

### 3.6 聊天界面模板

```html
{% extends "base.html" %}
{% block body %}
<div class="layui-container">
    <div class="layui-row">
        <div class="layui-col-md8 layui-col-md-offset2">
            <div class="layui-card">
                <div class="layui-card-header">智能问数</div>
                <div class="layui-card-body">
                    <div id="msg-box" style="height: 400px; overflow-y: auto;"></div>
                </div>
                <div class="layui-card-footer">
                    <div class="layui-input-group">
                        <input type="text" id="input-msg" class="layui-input" placeholder="输入你的问题...">
                        <div class="layui-input-group-btn">
                            <button class="layui-btn" id="btn-send">发送</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script>
layui.use(['layer'], function(){
    var layer = layui.layer;
    var ws = new WebSocket("ws://" + window.location.host + "/ws/chat");

    ws.onopen = function() { console.log("已连接"); };
    ws.onmessage = function(evt) {
        var data = JSON.parse(evt.data);
        var box = document.getElementById('msg-box');
        if (data.type === 'stream') {
            var last = box.lastElementChild;
            if (last && last.classList.contains('ai-msg')) {
                last.textContent += data.data;
            } else {
                var d = document.createElement('div');
                d.className = 'ai-msg';
                d.textContent = data.data;
                box.appendChild(d);
            }
        } else if (data.type === 'done') {
            box.scrollTop = box.scrollHeight;
        }
    };
    document.getElementById('btn-send').onclick = function() {
        var inp = document.getElementById('input-msg');
        var txt = inp.value.trim();
        if (!txt) return;
        var box = document.getElementById('msg-box');
        var d = document.createElement('div');
        d.className = 'user-msg';
        d.textContent = txt;
        box.appendChild(d);
        ws.send(JSON.stringify({type: 'message', data: txt}));
        inp.value = '';
        box.scrollTop = box.scrollHeight;
    };
});
</script>
{% end %}
```

### 3.7 错误提示

```html
{% if error %}
<div class="error">{{ error }}</div>
{% end %}
```

## 4. 路由配置

### 4.1 路由注册

在 `app.py` 的 `webapp()` 中配置：

```python
return tornado.web.Application([
    # ========== 用户端路由 ==========
    (r"/", LoginHandler),
    (r"/logout", LogoutHandler),
    (r"/index", IndexHandler),
    (r"/register", RegisterHandler),
    (r"/chat", ChatHandler),
    (r"/report", ReportHandler),
    (r"/history", HistoryHandler),
    (r"/export", ExportHandler),

    # ========== WebSocket 路由 ==========
    (r"/ws/chat", ChatWebSocketHandler),

    # ========== 管理端路由 ==========
    (r"/admin/login", AdminLoginHandler),
    (r"/admin/logout", AdminLogoutHandler),
    (r"/admin/index", AdminIndexHandler),
    (r"/admin/users", AdminUserHandler),
    (r"/admin/functions", AdminFunctionHandler),
    (r"/admin/menus", AdminMenuHandler),
    (r"/admin/roles", AdminRoleHandler),
    (r"/admin/watch", AdminWatchHandler),
    (r"/admin/data", AdminDataHandler),
    (r"/admin/collection", AdminCollectionHandler),
    (r"/admin/digital_employee", AdminDigitalEmployeeHandler),
    (r"/admin/model", AdminModelHandler),
    (r"/admin/dashboard", AdminDashboardHandler),
    (r"/admin/sentiment", AdminSentimentHandler),
], **settings)
```

### 4.2 前台路由表

| 路径 | Handler | 功能 | 需登录 |
|------|---------|------|--------|
| `/` | LoginHandler | 用户登录 | 否 |
| `/logout` | LogoutHandler | 用户登出 | 是 |
| `/index` | IndexHandler | 用户首页（chat.html） | 是 |
| `/register` | RegisterHandler | 用户注册 | 否 |
| `/ws/chat` | ChatWebSocketHandler | 实时对话 | 是 |
| `/api/models` | UserModelsAPIHandler | 模型列表API | 是 |
| `/api/employees` | UserEmployeesAPIHandler | 数字员工API | 是 |
| `/api/conversations` | UserConversationsAPIHandler | 对话列表/创建 | 是 |
| `/api/conversations/(\d+)` | UserConversationAPIHandler | 对话详情/删除 | 是 |

### 4.3 后台路由表

| 路径 | Handler | 功能 | 需登录 |
|------|---------|------|--------|
| `/admin/login` | AdminLoginHandler | 管理员登录 | 否 |
| `/admin/logout` | AdminLogoutHandler | 管理员登出 | 是 |
| `/admin/index` | AdminIndexHandler | 后台首页 | 是 |
| `/admin/users` | AdminUserHandler | 用户管理 | 是 |
| `/admin/functions` | AdminFunctionHandler | 功能管理 | 是 |
| `/admin/menus` | AdminMenuHandler | 菜单管理 | 是 |
| `/admin/roles` | AdminRoleHandler | 角色管理 | 是 |
| `/admin/watch` | AdminWatchHandler | 瞭望管理 | 是 |
| `/admin/data` | AdminDataHandler | 数据管理 | 是 |
| `/admin/collection` | AdminCollectionHandler | 采集管理 | 是 |
| `/admin/digital_employee` | AdminDigitalEmployeeHandler | 智能助手 | 是 |
| `/admin/model` | AdminModelHandler | 模型引擎 | 是 |
| `/admin/dashboard` | AdminDashboardHandler | 数智大屏 | 是 |
| `/admin/sentiment` | AdminSentimentHandler | 舆情大屏 | 是 |
| `/admin/digital_employee` | AdminDigitalEmployeeHandler | 数字员工 | 是 |
| `/admin/warehouse` | AdminWarehousePageHandler | 数据仓库 | 是 |
| `/admin/api/digital_employees` | AdminDigitalEmployeeAPIHandler | 数字员工API | 是 |
| `/admin/api/warehouse` | AdminWarehouseAPIHandler | 数据仓库API | 是 |
| `/admin/api/deep_collect` | AdminDeepCollectAPIHandler | 深度采集API | 是 |

## 5. 测试模板

```python
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.models.db import init_db
from app.models.user import UserRepository

init_db()

# 测试代码
print("测试结果:", result)
```

## 6. 文件命名

| 类型 | 规则 | 示例 |
|------|------|------|
| Controller | 小写_下划线 | auth.py, home.py |
| WebSocket | 小写_下划线 | chat.py |
| Model | 小写_下划线 | user.py, db.py |
| 大模型服务 | 小写_下划线 | llm_service.py |
| 智能助手 | 小写_下划线 | digital_employee.py |
| 模板 | 小写_下划线 | login.html, index.html |
| 测试 | 小写_下划线_case | test_user_models.py |
| CSS | 小写_下划线 | base.css |
| JS | 小写_下划线 | base.js |

## 7. 注释风格

### 7.1 文件头

```python
"""
模块说明：简短的模块功能描述
详细功能：
- 功能点 A
- 功能点 B
"""
```

### 7.2 类

```python
class UserRepository:
    """用户数据访问层 —— 为 Controller 提供数据处理方法"""
```

### 7.3 方法

```python
@staticmethod
def create_user(username: str, password: str) -> bool:
    """创建新用户。返回 True 表示成功，False 表示用户名已存在。"""
```

## 8. 配置文件模板

### 8.1 config/app.yaml

```yaml
server:
  host: "0.0.0.0"
  port: 10010
  debug: false
  autoreload: false

app:
  name: "DataFinderAgentOS"
  title: "智能瞭望与问数系统"
  version: "1.0.0"

session:
  cookie_secret: "change-this-in-production"
  login_url: "/"
  xsrf_cookies: true

template:
  path: "app/templates"

static:
  path: "app/static"
```

### 8.2 config/database.yaml

```yaml
database:
  type: "sqlite"
  path: "database/finderos.db"
  row_factory: "sqlite3.Row"

connection:
  timeout: 30
  check_same_thread: false
```

### 8.3 config/llm.yaml

```yaml
openai:
  api_key: "${OPENAI_API_KEY}"
  base_url: "https://api.openai.com/v1"
  model: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 4096
  stream: true

digital_employee:
  enabled: true
  commands:
    - "@天气"
    - "@新闻"
    - "@音乐"
    - "@电影"
    - "@川哥"
```

### 8.4 config/security.yaml

```yaml
password:
  hash_algorithm: "sha256"
  salt_length: 16
  iterations: 100000

session:
  max_age_days: 7
  secure: false
  httponly: true

rate_limit:
  login_max_attempts: 5
  login_lockout_minutes: 15
  websocket_max_messages_per_minute: 60

cors:
  allowed_origins: []

headers:
  x_frame_options: "SAMEORIGIN"
  x_xss_protection: "1; mode=block"
  x_content_type_options: "nosniff"
  strict_transport_security: "max-age=31536000"
```
