# DataFinderAgentOS 需求规格与跟踪

## 1. 系统概述

DataFinderAgentOS 是一款面向政务场景的智能瞭望与问数系统，基于 Tornado Web 框架构建 B/S 架构应用。系统划分为用户端（前台）和管理端（后台）两个子系统。

**用户端（前台）**: 用户通过对话式交互与数据直接"交流"，实现智能问答与数据分析，获取统计结果并生成可视化图表报告。

**管理端（后台）**: 为系统管理员提供全局管理能力，涵盖用户管理、权限配置、数据瞭望、采集调度、AI 引擎管理、可视化大屏等模块。

## 2. 功能需求列表

### 2.1 已实现功能

| 编号 | 功能说明 | 优先级 | 完成状态 | 关联文件 |
|------|----------|--------|----------|----------|
| REQ-001 | 用户登录认证 | 高 | ✅ | auth.py, login.html |
| REQ-002 | 用户登出 | 高 | ✅ | auth.py |
| REQ-003 | 用户首页 | 高 | ✅ | home.py, index.html |
| REQ-004 | 用户注册页面框架 | 中 | ✅ | register.html |
| REQ-005 | 用户数据持久化 | 高 | ✅ | user.py, db.py |
| REQ-006 | 密码哈希安全存储 | 高 | ✅ | user.py |
| REQ-007 | XSRF 安全防护 | 高 | ✅ | app.py, 模板 |
| REQ-008 | 安全 Cookie 会话管理 | 高 | ✅ | base.py, auth.py |
| REQ-010 | 管理员后台登录 | 高 | ✅ | admin.py, admin/login.html |
| REQ-011 | 后台管理首页 | 高 | ✅ | admin.py, admin/index.html |
| REQ-012 | 用户管理（后台） | 高 | ✅ | admin.py, admin/users.html, admin.py |
| REQ-031 | 功能权限管理 | 中 | ✅ | function.py, admin/functions.html |
| REQ-032 | 菜单配置管理 | 中 | ✅ | menu.py, admin/menus.html |
| REQ-033 | 角色权限管理 | 中 | ✅ | role.py, admin/roles.html |
| REQ-034 | 瞭望采集管理 | 高 | ✅ | watch.py, admin/watch.html |
| REQ-035 | 瞭源（数据源）管理 | 高 | ✅ | watch.py, admin/data.html |
| REQ-038 | AI 模型引擎管理（沉浸式暗色主题UI） | 高 | ✅ | model.py, admin/model.html |
| REQ-039 | 数据仓库管理 | 高 | ✅ | warehouse.py, admin/warehouse.html |
| REQ-050 | 数字员工管理 | 高 | ✅ | digital_employee.py, admin/digital_employee.html |
| REQ-051 | 深度采集（crawl4ai集成） | 高 | ✅ | deep_collect.py, admin/warehouse.html |
| REQ-052 | 用户端AI对话系统（ChatGPT风格） | 高 | ✅ | chat.py, chat.html, chat.css, chat.js, conversation.py, api.py |
| REQ-045 | 配置文件体系 | 高 | ✅ | config/ 目录 |

### 2.2 用户端待开发功能

| 编号 | 功能说明 | 优先级 | 状态 | 关联模块 |
|------|----------|--------|------|----------|
| REQ-009 | 用户注册后端逻辑 | 高 | ✅ | auth.py, user.py |
| REQ-016 | WebSocket 大模型对话 | 高 | ✅ | chat.py |
| REQ-017 | OpenAI API 集成 | 高 | ✅ | model.py, chat.py |
| REQ-018 | 对话界面（ChatGPT风格） | 高 | ✅ | chat.html, chat.css, chat.js |
| REQ-019 | 对话历史 | 中 | ✅ | conversation.py |
| REQ-021 | 智能助手 - @天气 | 中 | ✅ | digital_employee.py |
| REQ-022 | 智能助手 - @新闻 | 中 | ✅ | digital_employee.py |
| REQ-023 | 智能助手 - @音乐 | 中 | ✅ | digital_employee.py |
| REQ-024 | 智能助手 - @电影 | 中 | ✅ | digital_employee.py |
| REQ-025 | 智能助手 - @川哥 | 中 | ✅ | digital_employee.py |
| REQ-026 | 报表 - 统计分析 | 高 | 🔲 | 新增模块 |
| REQ-027 | 报表 - 图表生成 | 中 | 🔲 | 新增模块 |
| REQ-028 | 报告导出 | 中 | 🔲 | 新增模块 |
| REQ-029 | layui 前端重构 | 中 | 🔲 | 现有模板改造 |
| REQ-030 | 静态资源补全 | 低 | 🔲 | static/ 目录 |
| REQ-041 | 响应式移动端适配 | 高 | 🔲 | 全局模板 |
| REQ-042 | 沉浸式视觉风格 | 中 | 🔲 | CSS 样式 |
| REQ-043 | 自适应跨端方案 | 高 | 🔲 | 全局模板 |
| REQ-044 | OWASP Top 10 安全 | 高 | 🔲 | 安全模块 |
| REQ-045 | 配置文件体系 | 高 | ✅ | config/ 目录 |
| REQ-046 | 前台路由设计 | 高 | 🔲 | app.py |
| REQ-047 | 后台路由设计 | 高 | 🔲 | app.py |

### 2.3 管理端待开发功能

| 编号 | 功能说明 | 优先级 | 状态 | 关联模块 |
|------|----------|--------|------|----------|
| REQ-010 | 管理员后台登录 | 高 | 🔲 | admin/login.html |
| REQ-011 | 后台管理首页 | 高 | 🔲 | admin/index.html |
| REQ-012 | 用户管理 | 高 | 🔲 | user.py, admin/ |
| REQ-031 | 功能权限管理 | 中 | 🔲 | 新增模块 |
| REQ-032 | 菜单配置管理 | 中 | 🔲 | 新增模块 |
| REQ-033 | 角色权限管理 | 中 | 🔲 | 新增模块 |
| REQ-034 | 瞭望监控管理 | 高 | 🔲 | 新增模块 |
| REQ-035 | 数据源管理 | 高 | 🔲 | 新增模块 |
| REQ-036 | 采集调度管理 | 中 | 🔲 | 新增模块 |
| REQ-037 | 智能助手配置 | 中 | 🔲 | 新增模块 |
| REQ-038 | AI 模型管理 | 高 | 🔲 | 新增模块 |
| REQ-039 | 数智大屏 | 高 | 🔲 | 新增模块 |
| REQ-040 | 舆情分析大屏 | 高 | 🔲 | 新增模块 |

## 3. 功能详细说明

### REQ-001: 用户登录
- **功能**: 用户通过账号密码登录系统
- **输入**: 用户名（文本）、密码（密码）
- **输出**: 认证成功跳转首页，失败提示错误
- **校验规则**:
  - 用户名和密码不可为空
  - 用户名须在数据库中存在
  - 密码须与存储哈希匹配

### REQ-002: 用户登出
- **功能**: 用户退出登录状态
- **输入**: POST 到 /logout
- **输出**: 清除 Cookie，跳转登录页

### REQ-003: 首页展示
- **功能**: 登录后展示用户首页
- **输入**: 有效登录会话
- **输出**: 显示用户信息和功能入口
- **安全**: 需要 `@tornado.web.authenticated`

### REQ-005: 用户持久化
- **功能**: 用户数据存入 SQLite
- **表结构**: users(id, username, password_hash, salt, created_at)
- **约束**: username 唯一

### REQ-006: 密码安全
- **功能**: pbkdf2_hmac 哈希存储
- **算法**: sha256
- **salt**: 16 字节随机值
- **迭代**: 100,000 次

### REQ-016: WebSocket 对话
- **功能**: 提供 WebSocket 接口实现大模型实时对话
- **输入**: 用户消息（JSON）
- **输出**: 模型流式响应
- **协议**: `{"type": "message", "data": "用户输入"}`
- **安全**: 连接前校验登录态

### REQ-017: OpenAI 集成
- **功能**: 接入 OpenAI API 进行智能对话
- **输入**: 对话历史列表
- **输出**: 模型响应（流式）
- **配置**: API Key 通过环境变量注入
- **可选模型**: gpt-3.5-turbo, gpt-4 等

### REQ-018: 对话界面
- **功能**: 基于 layui 构建聊天 UI
- **包含**:
  - 消息列表展示区
  - 消息输入与发送
  - 流式响应实时渲染
  - 历史对话加载

### REQ-019: 对话历史
- **功能**: 记录用户与模型的对话
- **表结构**: conversations(id, user_id, messages, created_at, updated_at)
- **存储**: JSON 格式
- **查询**: 按用户检索历史

### REQ-021~025: 智能助手功能
- @天气：查询指定城市天气
- @新闻：获取新闻资讯
- @音乐：搜索音乐资源
- @电影：查询电影信息
- @川哥：触发特定响应

### REQ-026~028: 报表与导出
- 数据统计分析
- 可视化图表生成（柱状图、折线图、饼图）
- 报告导出（PDF、Word、Excel）

### REQ-031~040: 后台管理功能
- 用户管理、功能权限、菜单配置、角色权限
- 瞭望监控、数据源管理、采集调度
- 智能助手配置、AI 模型管理
- 数智大屏、舆情分析大屏

### REQ-034: 瞭望采集管理（已实现）
- **功能**: 通过配置化的瞭源规则，模拟浏览器请求采集全网资讯
- **页面布局**: A区（搜索输入区）+ B区（瞭源选择区）+ C区（橱窗结果区）
- **C区模式**: 橱窗列表模式，1行3列，每列12条（每页36条）
- **采集流程**: 用户输入关键词 → 勾选瞭源 → 采集按钮 → 后台线程异步执行 → 轮询结果
- **数据源**: watch_sources 表（支持RequestHeaders + URL参数配置）
- **采集器**: WatchCollector（支持占位符 {keyword} 和 {pn} 替换）
- **支持瞭源**: 百度新闻搜索、必应新闻、搜狗微信、360资讯、微博、知乎、人民网、新华网

### REQ-035: 瞭源管理（已实现）
- **功能**: 管理采集数据源的增删改查、启用/禁用
- **核心字段**: 名称、编码、类型（web/rss/api）、请求URL、URL参数（JSON）、请求头（JSON）、描述
- **URL参数模板**: 支持 `{keyword}` 和 `{pn}` 占位符，采集时自动替换
- **请求头**: 完整JSON格式的RequestHeaders，支持Cookie、User-Agent等
- **百度新闻规则**: base_url=`https://www.baidu.com/s`，params含rtt/bsst/cl/tn/rsv_dl等参数

### REQ-038: AI模型引擎管理（已实现 - 任务4增强）
- **功能**: 管理大语言模型配置，支持OpenAI兼容接口
- **模型参数**: 名称、Model ID、API Key、Base URL、Temperature、Max Tokens、Top P、Frequency/Presence Penalty、Provider（支持 OpenAI/Azure/Anthropic/Google/DeepSeek/Moonshot/智谱/通义千问/Custom）
- **Token统计**: 总Token、Prompt Token、Completion Token用量追踪，卡片内嵌可视化进度条
- **模型测试**: 内建SSE流式测试功能，实时输出模型响应（Markdown渲染），流式Token计数
- **默认模型**: 支持设默认模型，系统优先使用；默认模型卡片金色高亮
- **橱窗列表**: 卡片网格布局，分页支持，搜索过滤
- **UI风格**: 沉浸式暗色主题（#0a0a14底色），毛玻璃卡片，霓虹渐变发光边框，动画网格背景，Token进度条

### REQ-039: 数据仓库管理（已实现 - 任务3.2）
- **功能**: 存储和管理从瞭望采集系统保存的数据
- **列表展示**: layui表格列表，参考用户管理风格，支持分页/搜索/按来源筛选
- **数据来源**: C区采集结果支持勾选/全选后一键保存到数据仓库
- **操作**: 查看详情（弹窗）、删除（软删除）、深度采集标记
- **深度采集标识**: 列表中显示"是/否"深度采集标签
- **预留面板**: 深度采集任务面板（右侧悬浮窗模式，开发中占位）、深度采集数据查看（后续任务）

### REQ-050: 数字员工管理（已实现 - 任务5）
- **功能**: 管理两种类型的数字化员工，支持通过 @xxx 调度参与任务
- **类型一 - LLM 智能体**: 基于模型引擎中的默认模型或手动指派模型 + System Prompt + Skill 配置 + Crawl4AI 组件（可选），形成智能员工形态
- **类型二 - API 服务**: 基于 HTTP/HTTPS API + 请求参数 + 请求头 + 请求体 + 响应类型配置，支持通过接口直接响应数据
- **CRUD 操作**: 支持新增、编辑、删除、列表查看、分页、搜索
- **测试功能**: 编辑模式下支持实时测试（LLM类型发送消息测试，API类型发送请求测试）
- **UI风格**: 沉浸式暗色主题，霓虹发光卡片网格布局，类型选择器切换LLM/API配置面板
- **数据表**: digital_employees (name, code, type, model_id, prompt, skill_config, enable_crawl4ai, api_url, api_method, api_params, api_headers, api_body, response_type, icon, description, status, sort)
- **工作场景**: 深度采集任务可指派"采集专员"；前台 @天气 可调用天气API数字员工返回数据卡片

### REQ-051: 深度采集（已实现 - 任务3.3）
- **功能**: 对数据仓库中的URL进行深度网页内容采集，使用crawl4ai浏览器引擎获取完整网页内容
- **调度方式**: 通过数字员工-采集专员（enable_crawl4ai=1）执行采集任务
- **采集内容**: 网页标题、纯文本正文、HTML、Markdown、图片URL列表、字数统计
- **任务管理**: 创建任务、状态跟踪（pending/running/completed/failed）、进度百分比、步骤描述、执行日志
- **结果持久化**: 采集结果存入deep_collect_results表，关联任务ID和数据仓库记录ID
- **悬浮窗面板**: 右侧滑出面板，显示任务状态、进度条、当前步骤、数字员工信息、实时执行日志
- **批量采集**: 支持勾选多条数据仓库记录，批量启动深度采集任务
- **结果查看**: 已采集数据支持在面板中查看采集结果（正文/Markdown切换）
- **重新采集**: 已采集或采集失败的数据支持重新采集
- **数据表**: deep_collect_tasks (warehouse_id, employee_id, employee_name, url, title, status, progress, step, logs, result_id, error), deep_collect_results (task_id, warehouse_id, title, content, html, markdown, url, word_count, image_urls)
- **组件依赖**: crawl4ai + Playwright headless Chromium

### REQ-052: 用户端AI对话系统（已实现 - 任务6）
- **功能**: 重构用户端为ChatGPT/Doubao风格的智能对话系统
- **页面布局**: 左侧边栏（A区LOGO + B区模型切换 + C区对话列表）+ 右侧主区域（D区对话气泡 + E区输入框）
- **AI对话**: WebSocket流式通信，协程中调用模型API，支持打字机效果实时渲染
- **模型切换**: 下拉选择后台模型引擎中的可用模型，默认使用系统默认模型
- **@数字员工调度**: 输入框支持@code语法，自动弹出员工列表，调度LLM智能体或API服务型员工
- **/快捷功能**: 输入框支持/前缀激活快捷操作菜单（预留）
- **对话管理**: 自动创建对话、自动生成标题、历史对话列表、切换历史、删除对话
- **消息持久化**: conversations表 + chat_messages表，支持完整的对话历史存储
- **API接口**: GET /api/models（模型列表）、GET /api/employees（数字员工列表）、GET/POST /api/conversations（对话CRUD）、GET/DELETE /api/conversations/<id>（单对话操作）
- **视觉风格**: 浅色系企业政务风格，扁平化设计，自适应/响应式/沉浸式布局
- **登录注册**: 对接后台用户管理，完整的注册→登录→对话业务闭环
- **关联文件**: chat.py, chat.html, chat.css, chat.js, conversation.py, api.py, login.html, register.html, base.css

### REQ-044: OWASP 安全
- 覆盖 A01-A10 全部安全类型
- 访问控制、加密、注入防护、日志审计等

### REQ-045: 配置管理
- 集中管理于 config/ 目录
- 支持环境变量覆盖
- 敏感配置独立保护

## 4. 需求跟踪矩阵

| 编号 | 开发 | 测试 | 文档 |
|------|------|------|------|
| REQ-001 | ✅ | ✅ | ✅ |
| REQ-002 | ✅ | ✅ | ✅ |
| REQ-003 | ✅ | ✅ | ✅ |
| REQ-004 | ✅ | ⏳ | ✅ |
| REQ-005 | ✅ | ✅ | ✅ |
| REQ-006 | ✅ | ✅ | ✅ |
| REQ-007 | ✅ | ✅ | ✅ |
| REQ-008 | ✅ | ✅ | ✅ |
| REQ-009 | 🔲 | 🔲 | ✅ |
| REQ-010 | ✅ | ✅ | ✅ |
| REQ-011 | ✅ | ✅ | ✅ |
| REQ-012 | ✅ | ✅ | ✅ |
| REQ-031 | ✅ | ✅ | ✅ |
| REQ-032 | ✅ | ✅ | ✅ |
| REQ-033 | ✅ | ✅ | ✅ |
| REQ-034 | ✅ | ✅ | ✅ |
| REQ-035 | ✅ | ✅ | ✅ |
| REQ-038 | ✅ | ✅ | ✅ |
| REQ-039 | ✅ | ✅ | ✅ |
| REQ-050 | ✅ | ✅ | ✅ |
| REQ-051 | ✅ | ✅ | ✅ |
| REQ-052 | ✅ | ✅ | ✅ |
| REQ-045 | ✅ | ✅ | ✅ |
| REQ-016~030 | 🔲 | 🔲 | ✅ |
| REQ-036~040 | ⏳ | ⏳ | ✅ |
| REQ-041~047 | 🔲 | 🔲 | ✅ |

## 5. 变更记录

| 日期 | 内容 | 原因 |
|------|------|------|
| 2026-07-10 | 初始化需求文档 | 项目启动 |
| 2026-07-10 | 新增 WebSocket/OpenAI 对话需求 | 技术栈扩展 |
| 2026-07-10 | 补充用户端和管理端完整业务需求 | 范围扩展 |
| 2026-07-10 | 新增响应式设计和安全需求 | 设计规范扩展 |
| 2026-07-13 | 完成管理端核心模块：RBAC权限、瞭望采集、AI模型引擎 | 任务3开发 |
| 2026-07-13 | 瞭望采集实现百度新闻真实数据采集（RequestHeaders+URL参数） | 任务3-瞭望管理 |
| 2026-07-13 | 瞭源管理支持RequestHeaders和URL参数配置，支持占位符替换 | 任务3-瞭源管理 |
| 2026-07-13 | 采集结果改造为橱窗列表模式（1行3列，1列12条） | 任务3-UI改造 |
| 2026-07-13 | AI模型引擎管理增强：沉浸式暗色主题UI、Token可视化进度条、SSE流式测试升级、多Provider支持 | 任务4-模型引擎 |
| 2026-07-13 | 数据仓库模块：layui表格列表、查看/删除/深度采集标识、C区保存到仓库、深度采集悬浮窗预留 | 任务3.2-数据仓库 |
| 2026-07-15 | 数字员工管理：LLM智能体+API服务双类型、沉浸式UI、CRUD、测试功能、@调度预留 | 任务5-数字员工 |
| 2026-07-15 | 深度采集：crawl4ai浏览器引擎集成、采集专员调度、悬浮窗任务面板、批量采集、结果查看 | 任务3.3-深度采集 |
| 2026-07-15 | 用户端AI对话系统：ChatGPT风格界面、WebSocket流式对话、模型切换、@数字员工调度、对话历史管理、登录注册完善 | 任务6-用户端 |
