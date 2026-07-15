# DataFinderAgentOS —— 开发规范与约束条件

## 1. 技术选型约束

### 1.1 核心技术
- **编程语言**: Python 3.12+
- **Web 服务框架**: Tornado 6.x
- **数据存储**: SQLite3（Python 内建模块，零额外依赖）
- **模板渲染**: Tornado 内置模板引擎
- **前端 UI 库**: layui（优先使用）+ Bootstrap 5（辅助补充）
- **双向通信**: WebSocket（Tornado 原生支持）
- **AI 模型服务**: OpenAI API 接口

### 1.2 第三方依赖
- 优先采用 Python 标准库，尽量少引入外部依赖
- 如确需新依赖，统一在 venv 虚拟环境中通过 pip 安装
- OpenAI 调用需安装 `openai` 包

### 1.3 前端资源管理
- layui 与 Bootstrap 均已下载至 `app/static/dist/` 目录，离线可用
- **系统后台及前台页面首选 layui** 进行搭建
- **Bootstrap 仅作为**：辅助样式、特定布局场景的补充方案
- layui 官方文档参考：https://layui.dev/docs/2/

### 1.4 WebSocket 规范
- 基于 Tornado 的 `tornado.websocket.WebSocketHandler` 实现
- 建立 WebSocket 连接前须校验用户登录态
- 通信协议统一采用 JSON 格式
- 大模型对话必须走 WebSocket 实时通道

### 1.5 OpenAI 集成规范
- 通过 `openai` Python SDK 调用 API
- API Key 由环境变量或配置文件注入，严禁写死在代码中
- 必须支持 stream=True 流式输出以提供实时对话体验
- 对话历史由服务端统一管理或客户端本地缓存

### 1.6 智能助手规范
- 触发格式：`@功能名 参数`
- 内置功能：@天气、@新闻、@音乐、@电影、@川哥
- 指令解析优先级高于大模型通用对话
- 智能助手模块需独立封装，方便后续扩展
- 外部接口调用必须设置超时和异常处理

### 1.7 可视化大屏规范
- 数智大屏和舆情分析大屏基于 layui + ECharts 实现
- 大屏页面须适配高分辨率显示设备
- 数据需定时轮询刷新，支持实时更新
- 图表之间的联动交互通过 JS 实现

### 1.8 UI/UX 设计规范
- **响应式**: 借助 layui 和 Bootstrap 的栅格系统实现
- **视觉风格**: 暗色主题、渐变背景、卡片式布局、圆角元素
- **跨端适配**: 同时兼容移动设备（手机/平板）与桌面端
- **移动端**: 触控友好（按钮 ≥ 44px）、手势交互支持
- **桌面端**: 宽屏展示、多栏布局、鼠标悬停动效

### 1.9 配置管理规范
- 所有配置文件集中放在 `config/` 目录
- 采用 YAML 或 JSON 格式
- 敏感数据（密钥、API Key 等）独立管理
- 支持通过环境变量覆盖配置项

## 2. 架构约束

### 2.1 MVC 分层
项目严格遵循 MVC 架构：
- **Model 层** (`app/models/`): 数据库 CRUD 与业务逻辑
- **Controller 层** (`app/controllers/`): 请求分发与路由控制
- **View 层** (`app/templates/`): HTML 模板渲染

### 2.2 目录结构
```
DataFinderAgentOS/
├── app/              # MVC 业务代码
│   ├── controllers/  # 控制器，按业务模块拆分文件
│   ├── models/       # 数据模型
│   ├── static/       # 静态资源（CSS/JS）
│   │   ├── css/      # 自定义样式
│   │   ├── js/       # 自定义脚本
│   │   └── dist/     # 第三方 UI 框架
│   └── templates/    # 页面模板（含 admin/ 后台子目录）
├── config/           # 配置目录
│   ├── app.yaml
│   ├── database.yaml
│   ├── llm.yaml
│   └── security.yaml
├── database/         # SQLite 数据库文件
├── docs/             # 项目文档
├── test/             # 测试目录
└── venv/             # Python 虚拟环境
```

### 2.3 静态资源目录
```
app/static/dist/
├── bootstrap/      # Bootstrap 组件
│   ├── css/
│   └── js/
└── layui/          # layui 组件
    ├── css/
    ├── font/
    └── layui.js
```

## 3. 安全约束

### 3.1 密码安全
- 强制使用 `hashlib.pbkdf2_hmac("sha256", ...)` 进行哈希
- 每位用户生成独立随机 salt（16 字节）
- 迭代次数不低于 100,000

### 3.2 XSRF 防御
- 所有 POST 表单必须嵌入 `{% module xsrf_form_html() %}`
- 全局开启 `xsrf_cookies=True`

### 3.3 Cookie 安全
- 使用 `set_secure_cookie()` 写入会话 Cookie
- 配置 `cookie_secret` 用于签名防篡改
- 设置 `login_url` 统一拦截未登录请求

### 3.4 SQL 注入防护
- 全部 SQL 操作使用参数化查询（`?` 占位符）
- 严格禁止字符串拼接构造 SQL 语句

### 3.5 WebSocket 安全
- 连接建立时校验用户登录状态
- 消息体须做格式校验，防止恶意数据注入
- 限制单连接消息频率，避免刷屏攻击
- 异常断连后及时回收资源

### 3.6 大模型 API 安全
- API Key 不得以任何形式硬编码
- API Key 禁止出现在前端代码中
- 调用必须设置合理超时
- 敏感业务数据禁止发送给大模型

### 3.7 OWASP Top 10 防护

#### A01:2021 - 访问控制失效
- 实施 RBAC 角色权限模型
- 敏感操作均需权限校验
- 使用 `@tornado.web.authenticated` 保护页面路由
- 后台路由需额外管理员鉴权

#### A02:2021 - 加密机制缺陷
- 采用 pbkdf2_hmac(sha256) 做密码哈希
- 通过 HTTPS 传输敏感数据
- Cookie 设置 Secure 和 HttpOnly 标记
- API Key 使用高强度加密存储

#### A03:2021 - 注入攻击
- SQL 参数化查询防注入
- 用户输入严格校验与过滤
- 禁止 eval() 等危险函数
- 输出做 HTML 转义防 XSS

#### A04:2021 - 不安全设计
- 遵循最小权限原则
- 密码策略：最小长度、复杂度要求
- 会话超时自动失效
- 错误信息不暴露系统细节

#### A05:2021 - 安全配置错误
- 生产环境关闭 debug 模式
- 配置安全响应头
- 移除默认账户和弱密码
- 定期审查和更新配置

#### A06:2021 - 组件漏洞
- 及时更新 Python 依赖
- 移除未使用的依赖和组件
- 使用经过安全审计的第三方库
- 关注 CVE 漏洞公告

#### A07:2021 - 认证失效
- 强制强密码策略
- 支持密码重置流程
- 登录失败次数限制
- 安全的会话管理机制

#### A08:2021 - 数据完整性
- 安全的上传文件校验
- 关键数据完整性校验
- 使用版本控制管理代码
- 数据备份与恢复机制

#### A09:2021 - 日志监控
- 记录关键操作审计日志
- 异常行为实时监控
- 定期审查日志
- 配置告警规则

#### A10:2021 - SSRF 服务端请求伪造
- 校验所有外部 URL
- 允许访问的域名白名单
- 禁止用户控制的 URL 重定向
- 设置请求超时和流量限制

## 4. 代码规范

### 4.1 命名约定
- 文件名：snake_case（小写 + 下划线）
- 类名：CamelCase（大驼峰）
- 方法/函数名：snake_case
- 变量名：snake_case

### 4.2 格式要求
- 4 空格缩进
- 单行不超过 120 字符
- 逻辑块之间用空行分隔
- 尽量避免魔法数字，用常量或注释说明

### 4.3 异常处理
- 使用 try-except 捕获可预见的异常
- SQL 唯一键冲突统一捕获 `sqlite3.IntegrityError`

## 5. 运行环境

### 5.1 虚拟环境
- 项目须在 venv 环境中运行
- Windows 激活：`venv\Scripts\activate`

### 5.2 端口
- 默认监听 10010 端口
- 前台入口：http://localhost:10010/
- 后台入口：http://localhost:10010/admin/login

### 5.3 数据库
- 文件位置：`database/finderos.db`
- 路径由 `app/models/db.py` 统一管理

## 6. 开发指引

### 6.1 数据库操作
- 统一通过 `get_connection()` 获取连接
- 使用 `with get_connection() as conn` 上下文管理器确保自动关闭
- `row_factory` 设为 `sqlite3.Row`，支持按列名取值

### 6.2 Controller 开发
- 所有 Handler 继承 `BaseHandler`
- `get_current_user()` 由 `BaseHandler` 统一实现
- 需登录页面使用 `@tornado.web.authenticated` 装饰器

### 6.3 模板开发
- 前台模板继承 `base.html`
- 后台模板继承 `admin/base.html`
- 静态资源引用使用 `{{ static_url() }}`
- **前端框架优先级**：layui 组件 > Bootstrap 辅助

### 6.4 WebSocket Handler 开发
- 继承 `tornado.websocket.WebSocketHandler`
- 必须实现 `open()`、`on_message()`、`on_close()`
- 在 `open()` 中校验登录状态
- 消息格式：`{"type": "...", "data": "..."}`

### 6.5 大模型服务开发
- 使用 `openai.ChatCompletion.create()` 调用
- 开启流式：`stream=True`
- 消息历史格式：`[{"role": "user/assistant/system", "content": "..."}]`
- API 配置从环境变量或配置文件读取

### 6.6 智能助手开发
- 服务类命名：`DigitalEmployeeService`
- 命令通过字典映射注册
- 处理方法签名：`handle_command(args: str) -> str`
- 指令解析优先于大模型调用
- 两种类型：LLM智能体（模型+Prompt+Skill+Crawl4AI）、API服务（HTTP+参数+配置）
- 可通过 @code 编码调度数字员工参与业务执行

### 6.7 深度采集开发
- 使用 crawl4ai 库的 AsyncWebCrawler + BrowserConfig + CrawlerRunConfig 进行网页采集
- Playwright headless Chromium 浏览器须预先安装：`python -m playwright install chromium`
- 采集任务在独立线程中执行，通过 asyncio.run() 桥接异步 crawl4ai API
- 采集结果持久化到 deep_collect_tasks 和 deep_collect_results 表
- 通过数字员工-采集专员（enable_crawl4ai=1）调度执行
- SQLite 须开启 WAL 模式 + busy_timeout 以支持并发读写
- 数据库更新操作须加重试逻辑（最多3次），处理并发锁竞争

### 6.8 后台管理开发
- 路由前缀：`/admin/`
- 模板目录：`templates/admin/`
- 独立的登录态校验和权限控制
- 布局采用 layui admin 经典框架

### 6.9 路由系统规范

#### 路由前缀
- **前台路由**: `http://xxx/`（根路径）
- **后台路由**: `http://xxx/admin/`（admin 前缀）

#### 命名规则
- 路由使用小写字母 + 下划线
- 层级清晰，符合 RESTful 风格
- 后台路由统一以 `/admin/` 开头

#### 路由分组
- **用户侧**: 登录、注册、对话、报表、历史、导出
- **管理侧**: 用户管理、权限配置、数据管理、AI 引擎、大屏展示

#### 安全要求
- 前台需要登录的路由使用 `@tornado.web.authenticated`
- 所有后台路由均需管理员权限校验
- WebSocket 路由需登录态验证

## 7. 测试规范

### 7.1 测试目录
- 测试代码放在 `test/` 目录
- 文件命名：`xxx_case.py`

### 7.2 测试原则
- 测试前先调用 `init_db()` 初始化数据库
- 确保路径正确，通过 `sys.path` 加入项目根目录
