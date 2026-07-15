# DataFinderAgentOS 测试用例文档

## 1. 概述

测试覆盖以下维度：
- **功能测试**: 验证核心业务逻辑正确性
- **安全测试**: 验证安全防护机制有效性
- **数据库测试**: 验证数据存取正确性

## 2. 已有测试用例

### 2.1 用户模型测试

**文件**: `test/test_user_models.py`

| 编号 | 测试项 | 操作步骤 | 预期结果 |
|------|--------|----------|----------|
| TC-001 | 新建用户 | 执行 `UserRepository.create_user()` | 返回 `True` |
| TC-002 | 重复创建 | 相同用户名再次调用 `create_user()` | 返回 `False` |
| TC-003 | 正确密码校验 | 调用 `verify_user()` 传入正确密码 | 返回 `True` |
| TC-004 | 不存在用户 | 调用 `verify_user()` 传入不存在的用户名 | 返回 `False` |
| TC-005 | 错误密码校验 | 调用 `verify_user()` 传入错误密码 | 返回 `False` |

**测试代码**:

```python
import os
import sys
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.models.db import init_db
from app.models.user import UserRepository

init_db()

username = f"testuser_{int(time.time())}"
password = "123456"

print("新建1:", UserRepository.create_user(username, password))
print("新建2:", UserRepository.create_user(username, password))
print("验证正确:", UserRepository.verify_user(username, password))
print("验证错误:", UserRepository.verify_user("nobody", password))
print("验证错误:", UserRepository.verify_user(username, "wrong"))
```

**预期输出**:
```
新建1: True
新建2: False
验证正确: True
验证错误: False
验证错误: False
```

## 3. 待补充用例

### 3.1 Controller 测试

| 编号 | 测试项 | 操作步骤 | 预期结果 |
|------|--------|----------|----------|
| TC-006 | 空用户名登录 | POST 请求 username 为空 | 400 状态码 + 错误提示 |
| TC-007 | 空密码登录 | POST 请求 password 为空 | 400 状态码 + 错误提示 |
| TC-008 | 正常登录 | POST 正确用户名和密码 | 重定向至 /index |
| TC-009 | 密码错误 | POST 错误密码 | 401 状态码 + 错误提示 |

**登出测试**:

| 编号 | 测试项 | 操作步骤 | 预期结果 |
|------|--------|----------|----------|
| TC-010 | 正常登出 | POST /logout | Cookie 清除，重定向至 / |

### 3.2 深度采集测试

| 编号 | 测试项 | 操作步骤 | 预期结果 |
|------|--------|----------|----------|
| TC-016 | 创建深度采集任务 | POST /admin/api/deep_collect action=start record_id=有效ID | 返回task_id，任务状态pending→running→completed |
| TC-017 | 采集结果查询 | GET /admin/api/deep_collect?action=result&warehouse_id=有效ID | 返回标题、正文、HTML、Markdown、字数等信息 |
| TC-018 | 采集专员调度 | 启动深度采集，检查任务中的employee_name | 显示"采集专员"数字员工名称 |
| TC-019 | 批量深度采集 | POST action=batch_start record_ids=[id1,id2,id3] | 返回启动N个任务，跳过0个 |
| TC-020 | 采集进度轮询 | GET /admin/api/deep_collect?action=status&task_id=有效ID | 返回实时状态、进度百分比、步骤描述、执行日志 |
| TC-021 | 已采集查看 | 对已深度采集的记录点击"已采集"按钮 | 悬浮窗显示正文/Markdown内容 |

### 3.5 用户端对话系统测试

| 编号 | 测试项 | 操作步骤 | 预期结果 |
|------|--------|----------|----------|
| TC-022 | 用户注册 | POST /register username=新用户 password=密码 confirm_password=密码 | 302跳转至/，用户写入数据库 |
| TC-023 | 用户登录 | POST / username=testuser password=123456 | 302跳转至/index |
| TC-024 | 模型列表API | GET /api/models（已登录） | 返回JSON code=0, data含模型列表不含api_key |
| TC-025 | 数字员工API | GET /api/employees（已登录） | 返回JSON code=0, data含活跃员工列表 |
| TC-026 | 创建对话 | POST /api/conversations body={"title":"测试"} | 返回JSON code=0, data.id>0 |
| TC-027 | 对话列表 | GET /api/conversations | 返回JSON code=0, data为对话数组 |
| TC-028 | 获取消息 | GET /api/conversations/1?action=messages | 返回JSON code=0, data为消息数组 |
| TC-029 | 删除对话 | DELETE /api/conversations/1 | 返回JSON code=0, 对话及其消息被删除 |
| TC-030 | 聊天页面渲染 | GET /index（已登录） | 返回chat.html含chat-container/sidebar/input |

### 3.3 安全测试

| 编号 | 测试项 | 操作步骤 | 预期结果 |
|------|--------|----------|----------|
| TC-011 | XSRF 防护 | 无 XSRF token 发送 POST | 返回 403 |
| TC-012 | 未登录访问 | GET /index 无登录 Cookie | 重定向至 / |

### 3.4 数据库测试

| 编号 | 测试项 | 操作步骤 | 预期结果 |
|------|--------|----------|----------|
| TC-013 | 初始化建表 | 首次运行 `init_db()` | users 和 admins 表创建成功 |
| TC-014 | 查询存在用户 | `get_user_by_username()` 查询已存在的用户名 | 返回用户记录 |
| TC-015 | 查询不存在用户 | `get_user_by_username()` 查询不存在的用户名 | 返回 `None` |

## 4. 执行规范

### 4.1 环境要求
- Python 3.12+
- venv 虚拟环境
- SQLite 数据库文件：`database/finderos.db`

### 4.2 执行步骤
1. 激活虚拟环境：`venv\Scripts\activate`
2. 切换至项目根目录
3. 执行测试：`python test/xxx_case.py`

### 4.3 命名约定
- 测试文件：`xxx_case.py`
- 测试函数：`test_xxx()`
- 用例编号：`TC-xxx`

### 4.4 判定标准
- **通过**: 实际输出与预期全部一致
- **失败**: 存在实际输出与预期不一致
- **阻塞**: 环境问题导致无法执行

## 5. 覆盖率

### 5.1 已覆盖
- `app/models/user.py` —— 用户数据访问
- `app/models/db.py` —— 数据库初始化
- `app/models/deep_collect.py` —— 深度采集服务
- `app/models/conversation.py` —— 对话与消息数据访问
- `app/controllers/admin.py` —— 深度采集API
- `app/controllers/api.py` —— 用户端REST API
- `app/controllers/chat.py` —— WebSocket聊天处理器
- `app/controllers/home.py` —— 首页（chat.html）
- `app/templates/chat.html` —— 聊天界面模板
- `app/templates/login.html` —— 登录页模板
- `app/templates/register.html` —— 注册页模板
- `app/static/css/chat.css` —— 聊天界面样式
- `app/static/js/chat.js` —— 聊天界面脚本

### 5.2 未覆盖
- `app/controllers/auth.py` —— 认证控制器
- `app/controllers/home.py` —— 首页控制器
- `app/controllers/base.py` —— 基础控制器
- `app/templates/*.html` —— 模板页面

## 6. 测试记录

| 编号 | 日期 | 结果 | 备注 |
|------|------|------|------|
| TC-001 | 2026-07-10 | ✅ | 初始测试 |
| TC-002 | 2026-07-10 | ✅ | 初始测试 |
| TC-003 | 2026-07-10 | ✅ | 初始测试 |
| TC-004 | 2026-07-10 | ✅ | 初始测试 |
| TC-005 | 2026-07-10 | ✅ | 初始测试 |
| TC-016 | 2026-07-15 | ✅ | 深度采集任务创建与执行 |
| TC-017 | 2026-07-15 | ✅ | 深度采集结果持久化 |
| TC-018 | 2026-07-15 | ✅ | 采集专员数字员工调度 |
| TC-019 | 2026-07-15 | ✅ | 批量深度采集 |
| TC-022 | 2026-07-15 | ✅ | 用户注册 |
| TC-023 | 2026-07-15 | ✅ | 用户登录 |
| TC-024 | 2026-07-15 | ✅ | 模型列表API |
| TC-025 | 2026-07-15 | ✅ | 数字员工API |
| TC-026 | 2026-07-15 | ✅ | 创建对话 |
| TC-027 | 2026-07-15 | ✅ | 对话列表 |
| TC-028 | 2026-07-15 | ✅ | 获取消息 |
| TC-029 | 2026-07-15 | ✅ | 删除对话 |
| TC-030 | 2026-07-15 | ✅ | 聊天页面渲染 |
