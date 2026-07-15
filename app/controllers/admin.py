import json
import functools

import tornado.web

from app.models.admin import AdminRepository
from app.models.role import RoleRepository
from app.models.function import FunctionRepository
from app.models.menu import MenuRepository
from app.models.watch import WatchRepository, WatchCollector
from app.models.model import AIModelRepository, AIModelService
from app.models.warehouse import DataWarehouseRepository
from app.models.operation_log import OperationLogRepository
from app.models.digital_employee import DigitalEmployeeRepository, DigitalEmployeeService
from app.models.deep_collect import DeepCollectRepository, DeepCollectService


# ========== 装饰器：后台登录验证 ==========
def admin_auth(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.get_current_user():
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps({"code": 401, "msg": "请先登录"}))
                return
            self.redirect("/admin/login")
            return
        return method(self, *args, **kwargs)
    return wrapper


# ========== 后台基类 ==========
class AdminBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        admin = self.get_secure_cookie("admin")
        if not admin:
            return None
        return admin.decode("utf-8")

    def write_json(self, code=0, msg="", data=None, count=None):
        self.set_header("Content-Type", "application/json")
        result = {"code": code, "msg": msg}
        if data is not None:
            result["data"] = data
        if count is not None:
            result["count"] = count
        self.write(json.dumps(result, ensure_ascii=False))


# ========== 登录 / 登出 ==========
class AdminLoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("admin/login.html", title="后台管理登录", error=None)

    def post(self):
        username = self.get_body_argument("username", "")
        password = self.get_body_argument("password", "")
        ip = self.request.remote_ip

        if AdminRepository.verify_admin(username, password):
            self.set_secure_cookie("admin", username)
            OperationLogRepository.add(username, "admin", "登录", "管理员登录后台系统", ip)
            self.redirect("/admin/index")
        else:
            OperationLogRepository.add(username, "admin", "登录失败", "账号或密码不正确", ip)
            self.set_status(401)
            self.render("admin/login.html", title="后台管理登录", error="账号或密码不正确")


class AdminLogoutHandler(AdminBaseHandler):
    def post(self):
        username = self.get_current_user() or "unknown"
        OperationLogRepository.add(username, "admin", "登出", "管理员退出后台系统", self.request.remote_ip)
        self.clear_cookie("admin")
        self.redirect("/admin/login")


# ========== 系统首页 ==========
class AdminIndexHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/index.html", title="系统首页")


# ========== 页面渲染处理程序 ==========
class AdminUserHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/users.html", title="用户列表")


class AdminFunctionHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/functions.html", title="功能权限")


class AdminMenuHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/menus.html", title="菜单配置")


class AdminRoleHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/roles.html", title="角色权限")


# ========== 其他管理页面占位 ==========
class AdminWatchHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/watch.html", title="瞭望配置")


class AdminDataHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/data.html", title="数据源管理")


class AdminCollectionHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/collection.html", title="采集调度")


class AdminDigitalEmployeeHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/digital_employee.html", title="智能助手")


class AdminModelHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/model.html", title="模型管理")


class AdminDashboardHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/dashboard.html", title="数智大屏")


class AdminSentimentHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/sentiment.html", title="舆情分析")


class AdminWarehousePageHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        self.render("admin/warehouse.html", title="数据仓库")


# ========== API：用户管理 ==========
class AdminUserAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 10))
        keyword = self.get_argument("keyword", "")
        total, rows = AdminRepository.get_all(page, limit, keyword)
        data = []
        for r in rows:
            is_admin = bool(r["is_admin"])
            role_ids = AdminRepository.get_user_roles(r["id"]) if is_admin else []
            data.append({
                "id": r["id"],
                "username": r["username"],
                "is_admin": is_admin,
                "is_super": bool(r["is_super"]) if is_admin else False,
                "role_ids": role_ids,
                "created_at": r["created_at"],
            })
        self.write_json(data=data, count=total)

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        username = body.get("username", "").strip()
        password = body.get("password", "").strip()
        is_super = body.get("is_super", 0)
        role_ids = body.get("role_ids", [])
        if not username or not password:
            self.write_json(1, "用户名和密码不能为空")
            return
        # 检查前台用户表是否已有同名用户
        from app.models.user import UserRepository
        if UserRepository.get_user_by_username(username):
            self.write_json(1, "该用户名已被前台用户注册")
            return
        if not AdminRepository.create_admin(username, password, is_super):
            self.write_json(1, "用户名已存在")
            return
        admin = AdminRepository.get_admin_by_username(username)
        if admin and role_ids:
            AdminRepository.assign_roles(admin["id"], role_ids)
        OperationLogRepository.add(self.get_current_user(), "admin", "新增管理员", f"新增管理员: {username}", self.request.remote_ip)
        self.write_json(msg="新增成功")

    @admin_auth
    def put(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        admin_id = body.get("id")
        if not admin_id:
            self.write_json(1, "缺少用户ID")
            return
        # 只允许编辑管理员用户
        admin = AdminRepository.get_by_id(admin_id)
        if not admin:
            self.write_json(1, "前台注册用户不支持后台编辑，请在用户端操作")
            return
        password = body.get("password", "")
        is_super = body.get("is_super")
        role_ids = body.get("role_ids")
        AdminRepository.update_admin(admin_id, password, is_super)
        if role_ids is not None:
            AdminRepository.assign_roles(admin_id, role_ids)
        OperationLogRepository.add(self.get_current_user(), "admin", "编辑管理员", f"编辑管理员: {admin['username']}", self.request.remote_ip)
        self.write_json(msg="更新成功")

    @admin_auth
    def delete(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        admin_id = body.get("id")
        if not admin_id:
            self.write_json(1, "缺少用户ID")
            return
        admin = AdminRepository.get_by_id(admin_id)
        if not admin:
            self.write_json(1, "前台注册用户不支持后台删除")
            return
        if admin["username"] == "root":
            self.write_json(1, "不能删除超级管理员 root")
            return
        AdminRepository.delete_admin(admin_id)
        OperationLogRepository.add(self.get_current_user(), "admin", "删除管理员", f"删除管理员: {admin['username']}", self.request.remote_ip)
        self.write_json(msg="删除成功")


# ========== API：角色管理 ==========
class AdminRoleAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 10))
        keyword = self.get_argument("keyword", "")
        all_roles = RoleRepository.get_all()
        if keyword:
            all_roles = [r for r in all_roles if keyword in r["name"] or keyword in r["code"]]
        total = len(all_roles)
        start = (page - 1) * limit
        end = start + limit
        page_roles = all_roles[start:end]
        data = []
        for r in page_roles:
            func_ids = RoleRepository.get_role_functions(r["id"])
            menu_ids = RoleRepository.get_role_menus(r["id"])
            data.append({
                "id": r["id"],
                "name": r["name"],
                "code": r["code"],
                "description": r["description"],
                "status": r["status"],
                "function_ids": func_ids,
                "menu_ids": menu_ids,
                "created_at": r["created_at"],
            })
        self.write_json(data=data, count=total)

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        name = body.get("name", "").strip()
        code = body.get("code", "").strip()
        description = body.get("description", "")
        status = body.get("status", 1)
        function_ids = body.get("function_ids", [])
        menu_ids = body.get("menu_ids", [])
        if not name or not code:
            self.write_json(1, "角色名称和编码不能为空")
            return
        if not RoleRepository.create(name, code, description, status):
            self.write_json(1, "角色编码已存在")
            return
        all_roles = RoleRepository.get_all()
        new_role = all_roles[-1] if all_roles else None
        if new_role:
            RoleRepository.assign_functions(new_role["id"], function_ids)
            RoleRepository.assign_menus(new_role["id"], menu_ids)
        OperationLogRepository.add(self.get_current_user(), "admin", "新增角色", f"新增角色: {name}", self.request.remote_ip)
        self.write_json(msg="新增成功")

    @admin_auth
    def put(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        role_id = body.get("id")
        if not role_id:
            self.write_json(1, "缺少角色ID")
            return
        name = body.get("name", "").strip()
        code = body.get("code", "").strip()
        description = body.get("description", "")
        status = body.get("status", 1)
        function_ids = body.get("function_ids")
        menu_ids = body.get("menu_ids")
        if not RoleRepository.update(role_id, name, code, description, status):
            self.write_json(1, "角色编码已存在")
            return
        if function_ids is not None:
            RoleRepository.assign_functions(role_id, function_ids)
        if menu_ids is not None:
            RoleRepository.assign_menus(role_id, menu_ids)
        OperationLogRepository.add(self.get_current_user(), "admin", "编辑角色", f"编辑角色: {name}", self.request.remote_ip)
        self.write_json(msg="更新成功")

    @admin_auth
    def delete(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        role_id = body.get("id")
        if not role_id:
            self.write_json(1, "缺少角色ID")
            return
        role = RoleRepository.get_by_id(role_id)
        if role and role["code"] == "super_admin":
            self.write_json(1, "不能删除超级管理员角色")
            return
        RoleRepository.delete(role_id)
        OperationLogRepository.add(self.get_current_user(), "admin", "删除角色", f"删除角色: {role['name']}", self.request.remote_ip)
        self.write_json(msg="删除成功")


# ========== API：功能管理 ==========
class AdminFunctionAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        all_funcs = FunctionRepository.get_all()
        data = []
        for f in all_funcs:
            data.append({
                "id": f["id"],
                "name": f["name"],
                "code": f["code"],
                "url": f["url"],
                "method": f["method"],
                "parent_id": f["parent_id"],
                "type": f["type"],
                "sort": f["sort"],
                "status": f["status"],
                "created_at": f["created_at"],
            })
        self.write_json(data=data)

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        name = body.get("name", "").strip()
        code = body.get("code", "").strip()
        if not name or not code:
            self.write_json(1, "功能名称和编码不能为空")
            return
        if not FunctionRepository.create(
            name, code,
            body.get("url", ""),
            body.get("method", "GET"),
            body.get("parent_id", 0),
            body.get("type", "menu"),
            body.get("sort", 0),
            body.get("status", 1),
        ):
            self.write_json(1, "功能编码已存在")
            return
        OperationLogRepository.add(self.get_current_user(), "admin", "新增功能", f"新增功能: {name}", self.request.remote_ip)
        self.write_json(msg="新增成功")

    @admin_auth
    def put(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        func_id = body.get("id")
        if not func_id:
            self.write_json(1, "缺少功能ID")
            return
        if not FunctionRepository.update(
            func_id,
            body.get("name", "").strip(),
            body.get("code", "").strip(),
            body.get("url", ""),
            body.get("method", "GET"),
            body.get("parent_id", 0),
            body.get("type", "menu"),
            body.get("sort", 0),
            body.get("status", 1),
        ):
            self.write_json(1, "功能编码已存在")
            return
        OperationLogRepository.add(self.get_current_user(), "admin", "编辑功能", f"编辑功能: {body.get('name', '').strip()}", self.request.remote_ip)
        self.write_json(msg="更新成功")

    @admin_auth
    def delete(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        func_id = body.get("id")
        if not func_id:
            self.write_json(1, "缺少功能ID")
            return
        FunctionRepository.delete(func_id)
        OperationLogRepository.add(self.get_current_user(), "admin", "删除功能", f"删除功能ID: {func_id}", self.request.remote_ip)
        self.write_json(msg="删除成功")


# ========== API：菜单管理 ==========
class AdminMenuAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        all_menus = MenuRepository.get_all()
        data = []
        for m in all_menus:
            data.append({
                "id": m["id"],
                "name": m["name"],
                "icon": m["icon"],
                "url": m["url"],
                "parent_id": m["parent_id"],
                "sort": m["sort"],
                "status": m["status"],
                "created_at": m["created_at"],
            })
        self.write_json(data=data)

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        name = body.get("name", "").strip()
        if not name:
            self.write_json(1, "菜单名称不能为空")
            return
        MenuRepository.create(
            name,
            body.get("icon", ""),
            body.get("url", ""),
            body.get("parent_id", 0),
            body.get("sort", 0),
            body.get("status", 1),
        )
        OperationLogRepository.add(self.get_current_user(), "admin", "新增菜单", f"新增菜单: {name}", self.request.remote_ip)
        self.write_json(msg="新增成功")

    @admin_auth
    def put(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        menu_id = body.get("id")
        if not menu_id:
            self.write_json(1, "缺少菜单ID")
            return
        MenuRepository.update(
            menu_id,
            body.get("name", "").strip(),
            body.get("icon", ""),
            body.get("url", ""),
            body.get("parent_id", 0),
            body.get("sort", 0),
            body.get("status", 1),
        )
        OperationLogRepository.add(self.get_current_user(), "admin", "编辑菜单", f"编辑菜单: {body.get('name', '').strip()}", self.request.remote_ip)
        self.write_json(msg="更新成功")

    @admin_auth
    def delete(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        menu_id = body.get("id")
        if not menu_id:
            self.write_json(1, "缺少菜单ID")
            return
        MenuRepository.delete(menu_id)
        OperationLogRepository.add(self.get_current_user(), "admin", "删除菜单", f"删除菜单ID: {menu_id}", self.request.remote_ip)
        self.write_json(msg="删除成功")


# ========== API：获取角色/功能/菜单树（供表单选择） ==========
class AdminTreeDataHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        funcs = FunctionRepository.get_all()
        menus = MenuRepository.get_all()
        roles = RoleRepository.get_all()

        func_tree = []
        for f in funcs:
            func_tree.append({
                "id": f["id"],
                "name": f["name"],
                "code": f["code"],
                "parent_id": f["parent_id"],
                "type": f["type"],
            })

        menu_tree = []
        for m in menus:
            menu_tree.append({
                "id": m["id"],
                "name": m["name"],
                "parent_id": m["parent_id"],
            })

        role_list = [{"id": r["id"], "name": r["name"], "code": r["code"]} for r in roles]

        self.write_json(data={
            "functions": func_tree,
            "menus": menu_tree,
            "roles": role_list,
        })


# ========== API：瞭望系统 —— 瞭源管理 ==========
class AdminWatchSourceAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        sources = WatchRepository.get_all_sources()
        data = []
        for s in sources:
            data.append({
                "id": s["id"], "name": s["name"], "code": s["code"],
                "source_type": s["source_type"], "base_url": s["base_url"],
                "status": s["status"], "config": s["config"], "sort": s["sort"],
                "description": s["description"], "request_headers": s["request_headers"],
                "params": s["params"], "created_at": s["created_at"],
            })
        self.write_json(data=data)

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        name = body.get("name", "").strip()
        code = body.get("code", "").strip()
        if not name or not code:
            self.write_json(1, "名称和编码不能为空")
            return
        if not WatchRepository.create_source(
            name, code,
            body.get("source_type", "web"),
            body.get("base_url", ""),
            body.get("status", 1),
            body.get("config", "{}"),
            body.get("sort", 0),
            body.get("description", ""),
            body.get("request_headers", "{}"),
            body.get("params", "{}"),
        ):
            self.write_json(1, "编码已存在")
            return
        OperationLogRepository.add(self.get_current_user(), "admin", "新增瞭源", f"新增瞭源: {name}", self.request.remote_ip)
        self.write_json(msg="新增成功")

    @admin_auth
    def put(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        sid = body.get("id")
        if not sid:
            self.write_json(1, "缺少ID")
            return
        kwargs = {}
        for k in ["name", "code", "source_type", "base_url", "status", "config", "sort", "description", "request_headers", "params"]:
            if k in body:
                kwargs[k] = body[k]
        WatchRepository.update_source(sid, **kwargs)
        OperationLogRepository.add(self.get_current_user(), "admin", "编辑瞭源", f"编辑瞭源: {body.get('name', '')}", self.request.remote_ip)
        self.write_json(msg="更新成功")

    @admin_auth
    def delete(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        sid = body.get("id")
        if not sid:
            self.write_json(1, "缺少ID")
            return
        WatchRepository.delete_source(sid)
        OperationLogRepository.add(self.get_current_user(), "admin", "删除瞭源", f"删除瞭源ID: {sid}", self.request.remote_ip)
        self.write_json(msg="删除成功")


# ========== API：瞭望系统 —— 采集任务 ==========
class AdminWatchTaskAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        tasks = WatchRepository.get_latest_tasks(20)
        data = []
        for t in tasks:
            data.append({
                "id": t["id"], "keyword": t["keyword"],
                "source_ids": t["source_ids"], "status": t["status"],
                "total_count": t["total_count"], "created_at": t["created_at"],
            })
        self.write_json(data=data)

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        keyword = body.get("keyword", "").strip()
        source_ids = body.get("source_ids", [])
        if not keyword:
            self.write_json(1, "请输入关键字")
            return
        if not source_ids:
            self.write_json(1, "请选择至少一个瞭源")
            return
        task_id = WatchRepository.create_task(keyword, source_ids)
        # 异步执行采集
        import threading
        t = threading.Thread(target=WatchRepository.execute_collection, args=(task_id,))
        t.start()
        OperationLogRepository.add(self.get_current_user(), "admin", "采集任务", f"提交瞭望采集任务: {keyword}", self.request.remote_ip)
        self.write_json(data={"task_id": task_id}, msg="采集任务已提交")


# ========== API：瞭望系统 —— 采集结果 ==========
class AdminWatchResultAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        task_id = int(self.get_argument("task_id", 0))
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 15))
        if not task_id:
            self.write_json(1, "缺少任务ID")
            return
        task = WatchRepository.get_task_by_id(task_id)
        if not task:
            self.write_json(1, "任务不存在")
            return
        if task["status"] == "running":
            self.write_json(1, "采集中，请稍候...")
            return
        if task["status"] == "failed":
            self.write_json(1, "采集失败")
            return
        total, rows = WatchRepository.get_results(task_id, page, limit)
        data = []
        for r in rows:
            data.append({
                "id": r["id"], "task_id": r["task_id"],
                "source_id": r["source_id"], "source_name": r["source_name"],
                "title": r["title"], "url": r["url"],
                "summary": r["summary"], "collected_at": r["collected_at"],
            })
        self.write_json(data=data, count=total)


# ========== API：操作日志 ==========
class AdminLogAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        limit = int(self.get_argument("limit", 10))
        rows = OperationLogRepository.get_recent(limit)
        data = []
        for r in rows:
            data.append({
                "id": r["id"],
                "username": r["username"],
                "user_type": r["user_type"],
                "action": r["action"],
                "detail": r["detail"],
                "ip_address": r["ip_address"],
                "created_at": r["created_at"],
            })
        self.write_json(data=data)


# ========== API：AI 模型引擎管理 ==========
class AdminModelAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        action = self.get_argument("action", "list")
        if action == "detail":
            model_id = int(self.get_argument("id", 0))
            model = AIModelRepository.get_model_by_id(model_id)
            if model:
                self.write_json(data=model)
            else:
                self.write_json(1, "模型不存在")
        else:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("page_size", 12))
            keyword = self.get_argument("keyword", "")
            models, total = AIModelRepository.get_models(page=page, page_size=page_size, keyword=keyword)
            token_stats = AIModelRepository.get_token_stats()
            self.write_json(data={"models": models, "total": total, "token_stats": token_stats})

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        action = body.get("action", "add")

        if action == "add":
            name = body.get("name", "").strip()
            model_id = body.get("model_id", "").strip()
            api_key = body.get("api_key", "").strip()
            base_url = body.get("base_url", "").strip()
            if not name or not model_id or not api_key or not base_url:
                self.write_json(1, "模型名称/ID/API Key/Base URL 不能为空")
                return
            if AIModelRepository.create_model(
                name, model_id, api_key, base_url,
                float(body.get("temperature", 0.7)),
                int(body.get("max_tokens", 4096)),
                float(body.get("top_p", 0.9)),
                float(body.get("frequency_penalty", 0.0)),
                float(body.get("presence_penalty", 0.0)),
                body.get("description", ""),
                body.get("provider", "openai"),
            ):
                OperationLogRepository.add(self.get_current_user(), "admin", "新增模型", f"新增AI模型: {name}", self.request.remote_ip)
                self.write_json(msg="模型添加成功")
            else:
                self.write_json(1, "模型名称已存在")

        elif action == "edit":
            model_db_id = int(body.get("id", 0))
            if AIModelRepository.update_model(
                model_db_id,
                body.get("name", "").strip(),
                body.get("model_id", "").strip(),
                body.get("api_key", "").strip(),
                body.get("base_url", "").strip(),
                float(body.get("temperature", 0.7)),
                int(body.get("max_tokens", 4096)),
                float(body.get("top_p", 0.9)),
                float(body.get("frequency_penalty", 0.0)),
                float(body.get("presence_penalty", 0.0)),
                body.get("description", ""),
                body.get("provider", "openai"),
            ):
                OperationLogRepository.add(self.get_current_user(), "admin", "编辑模型", f"编辑AI模型: {body.get('name', '')}", self.request.remote_ip)
                self.write_json(msg="模型更新成功")
            else:
                self.write_json(1, "模型名称已存在")

        elif action == "delete":
            model_db_id = int(body.get("id", 0))
            AIModelRepository.delete_model(model_db_id)
            OperationLogRepository.add(self.get_current_user(), "admin", "删除模型", f"删除AI模型ID: {model_db_id}", self.request.remote_ip)
            self.write_json(msg="模型删除成功")

        elif action == "set_default":
            model_db_id = int(body.get("id", 0))
            AIModelRepository.set_default_model(model_db_id)
            OperationLogRepository.add(self.get_current_user(), "admin", "设置默认模型", f"设置默认AI模型ID: {model_db_id}", self.request.remote_ip)
            self.write_json(msg="默认模型设置成功")

        elif action == "toggle":
            model_db_id = int(body.get("id", 0))
            status = int(body.get("status", 0))
            AIModelRepository.toggle_model_status(model_db_id, status)
            self.write_json(msg="状态更新成功")

        elif action == "test":
            model_db_id = int(body.get("id", 0))
            model = AIModelRepository.get_model_by_id(model_db_id)
            if model:
                result = AIModelService.test_model(model)
                if result["success"]:
                    AIModelRepository.update_tokens(model_db_id, result["prompt_tokens"], result["completion_tokens"])
                self.write_json(data=result)
            else:
                self.write_json(1, "模型不存在")


# ========== API：AI 模型流式测试 ==========
class AdminModelTestHandler(AdminBaseHandler):
    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return

        model_id = int(body.get("model_id", 0))
        prompt = body.get("prompt", "")

        model = AIModelRepository.get_model_by_id(model_id)
        if not model:
            self.set_header("Content-Type", "text/event-stream")
            self.set_header("Cache-Control", "no-cache")
            self.set_header("Connection", "keep-alive")
            self.write(f"data: {json.dumps({'type': 'error', 'message': '模型不存在'})}\n\n")
            self.finish()
            return

        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")

        messages = [{"role": "user", "content": prompt}]
        full_content = ""
        prompt_tokens = AIModelService.estimate_tokens(prompt)
        completion_tokens = 0

        try:
            for chunk in AIModelService.chat_completion(model, messages):
                if "choices" in chunk and chunk["choices"]:
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        full_content += content
                        completion_tokens += AIModelService.estimate_tokens(content)
                        data = {
                            'type': 'token',
                            'content': content,
                            'prompt_tokens': prompt_tokens,
                            'completion_tokens': completion_tokens,
                            'total_tokens': prompt_tokens + completion_tokens
                        }
                        self.write(f"data: {json.dumps(data)}\n\n")
                        self.flush()
            done_data = {
                'type': 'done',
                'content': full_content,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens
            }
            self.write(f"data: {json.dumps(done_data)}\n\n")
            AIModelRepository.update_tokens(model_id, prompt_tokens, completion_tokens)
        except Exception as e:
            self.write(f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n")
        self.finish()


# ========== API：数字员工管理 ==========
class AdminDigitalEmployeeAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 10))
        keyword = self.get_argument("keyword", "")
        action = self.get_argument("action", "list")

        if action == "detail":
            emp_id = int(self.get_argument("id", 0))
            emp = DigitalEmployeeRepository.get_by_id(emp_id)
            if emp:
                self.write_json(data=emp)
            else:
                self.write_json(1, "数字员工不存在")
        elif action == "models":
            from app.models.model import AIModelRepository
            models, _ = AIModelRepository.get_models(page=1, page_size=100)
            data = [{"id": m["id"], "name": m["name"], "model_id": m["model_id"],
                     "is_default": m["is_default"]} for m in models]
            self.write_json(data=data)
        else:
            rows, total = DigitalEmployeeRepository.get_all(page=page, page_size=page_size, keyword=keyword)
            self.write_json(data=rows, count=total)

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        action = body.get("action", "add")

        if action == "add":
            name = body.get("name", "").strip()
            code = body.get("code", "").strip()
            if not name or not code:
                self.write_json(1, "名称和编码不能为空")
                return
            if not DigitalEmployeeRepository.create(
                name=name, code=code,
                emp_type=body.get("type", "llm"),
                model_id=int(body.get("model_id", 0)),
                prompt=body.get("prompt", ""),
                skill_config=body.get("skill_config", "{}"),
                enable_crawl4ai=int(body.get("enable_crawl4ai", 0)),
                api_url=body.get("api_url", ""),
                api_method=body.get("api_method", "GET"),
                api_params=body.get("api_params", "{}"),
                api_headers=body.get("api_headers", "{}"),
                api_body=body.get("api_body", "{}"),
                response_type=body.get("response_type", "json"),
                icon=body.get("icon", "fas fa-robot"),
                description=body.get("description", ""),
                status=int(body.get("status", 1)),
                sort=int(body.get("sort", 0)),
            ):
                self.write_json(1, "编码已存在")
                return
            OperationLogRepository.add(self.get_current_user(), "admin", "新增数字员工", f"新增数字员工: {name}", self.request.remote_ip)
            self.write_json(msg="新增成功")

        elif action == "edit":
            emp_id = int(body.get("id", 0))
            if not emp_id:
                self.write_json(1, "缺少ID")
                return
            kwargs = {}
            for k in ["name", "code", "type", "model_id", "prompt", "skill_config",
                       "enable_crawl4ai", "api_url", "api_method", "api_params",
                       "api_headers", "api_body", "response_type", "icon",
                       "description", "status", "sort"]:
                if k in body:
                    val = body[k]
                    if k in ("model_id", "enable_crawl4ai", "status", "sort"):
                        val = int(val) if val is not None else 0
                    kwargs[k] = val
            DigitalEmployeeRepository.update(emp_id, **kwargs)
            OperationLogRepository.add(self.get_current_user(), "admin", "编辑数字员工", f"编辑数字员工: {body.get('name', '')}", self.request.remote_ip)
            self.write_json(msg="更新成功")

        elif action == "delete":
            emp_id = int(body.get("id", 0))
            if not emp_id:
                self.write_json(1, "缺少ID")
                return
            DigitalEmployeeRepository.delete(emp_id)
            OperationLogRepository.add(self.get_current_user(), "admin", "删除数字员工", f"删除数字员工ID: {emp_id}", self.request.remote_ip)
            self.write_json(msg="删除成功")

        elif action == "toggle":
            emp_id = int(body.get("id", 0))
            status = int(body.get("status", 0))
            DigitalEmployeeRepository.update(emp_id, status=status)
            self.write_json(msg="状态更新成功")

        elif action == "test":
            emp_id = int(body.get("id", 0))
            emp = DigitalEmployeeRepository.get_by_id(emp_id)
            if not emp:
                self.write_json(1, "数字员工不存在")
                return
            test_message = body.get("message", "你好，请介绍一下自己")
            test_params = body.get("params", {})
            result = DigitalEmployeeService.execute(emp, user_message=test_message, params=test_params)
            self.write_json(data=result)


# ========== API：数据仓库管理 ==========
class AdminWarehouseAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 20))
        keyword = self.get_argument("keyword", "")
        source = self.get_argument("source", "")
        action = self.get_argument("action", "list")

        if action == "detail":
            record_id = int(self.get_argument("id", 0))
            record = DataWarehouseRepository.get_record_by_id(record_id)
            if record:
                self.write_json(data=record)
            else:
                self.write_json(1, "记录不存在")
        else:
            records, total = DataWarehouseRepository.get_records(page=page, page_size=page_size, keyword=keyword, source=source)
            stats = DataWarehouseRepository.get_stats()
            self.write_json(data={"records": records, "total": total, "stats": stats})

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        action = body.get("action", "")

        if action == "delete":
            record_id = int(body.get("id", 0))
            DataWarehouseRepository.delete_record(record_id)
            self.write_json(msg="删除成功")

        elif action == "deep_collect":
            record_id = int(body.get("id", 0))
            DataWarehouseRepository.mark_deep_collected(record_id)
            self.write_json(msg="深度采集已标记")

        elif action == "save_to_warehouse":
            articles = body.get("articles", [])
            source_name = body.get("source_name", "")
            keyword = body.get("keyword", "")
            try:
                records = []
                for article in articles:
                    records.append((
                        article.get("title", ""),
                        article.get("summary", article.get("description", "")),
                        "",
                        article.get("url", ""),
                        source_name,
                        0,
                        keyword,
                        article.get("image_url", article.get("image", ""))
                    ))
                DataWarehouseRepository.add_records(records)
                OperationLogRepository.add(self.get_current_user(), "admin", "保存数据", f"保存{len(records)}条数据到仓库", self.request.remote_ip)
                self.write_json(msg=f"成功保存 {len(records)} 条数据到仓库")
            except Exception as e:
                self.write_json(1, str(e))


# ========== API：深度采集管理 ==========
class AdminDeepCollectAPIHandler(AdminBaseHandler):
    @admin_auth
    def get(self):
        action = self.get_argument("action", "status")
        task_id = int(self.get_argument("task_id", 0))
        warehouse_id = int(self.get_argument("warehouse_id", 0))

        if action == "status":
            if task_id:
                task = DeepCollectRepository.get_task(task_id)
                if task:
                    task["logs_parsed"] = []
                    try:
                        import json
                        task["logs_parsed"] = json.loads(task.get("logs", "[]"))
                    except (json.JSONDecodeError, TypeError):
                        pass
                    self.write_json(data=task)
                else:
                    self.write_json(1, "任务不存在")
            elif warehouse_id:
                tasks = DeepCollectRepository.get_tasks_by_warehouse(warehouse_id)
                for t in tasks:
                    try:
                        import json
                        t["logs_parsed"] = json.loads(t.get("logs", "[]"))
                    except (json.JSONDecodeError, TypeError):
                        t["logs_parsed"] = []
                self.write_json(data=tasks)
            else:
                page = int(self.get_argument("page", 1))
                page_size = int(self.get_argument("page_size", 20))
                tasks, total = DeepCollectRepository.get_all_tasks(page, page_size)
                self.write_json(data=tasks, count=total)

        elif action == "result":
            if task_id:
                result = DeepCollectRepository.get_result_by_task(task_id)
                if result:
                    self.write_json(data=result)
                else:
                    self.write_json(1, "结果不存在")
            elif warehouse_id:
                result = DeepCollectRepository.get_result_by_warehouse(warehouse_id)
                if result:
                    self.write_json(data=result)
                else:
                    self.write_json(1, "结果不存在")
            else:
                self.write_json(1, "缺少task_id或warehouse_id")

        elif action == "collector_status":
            emp = DeepCollectService._get_collector_employee()
            self.write_json(data={"available": emp is not None, "employee": emp})

    @admin_auth
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_json(1, "请求数据格式错误")
            return
        action = body.get("action", "start")

        if action == "start":
            record_id = int(body.get("record_id", 0))
            if not record_id:
                self.write_json(1, "缺少数据记录ID")
                return
            record = DataWarehouseRepository.get_record_by_id(record_id)
            if not record:
                self.write_json(1, "数据记录不存在")
                return
            url = record.get("url", "")
            if not url:
                self.write_json(1, "该数据记录没有URL，无法深度采集")
                return

            # Check if already has a running task
            existing_tasks = DeepCollectRepository.get_tasks_by_warehouse(record_id)
            for t in existing_tasks:
                if t["status"] in ("pending", "running"):
                    self.write_json(1, f"该数据已有进行中的采集任务（任务ID: {t['id']}）")
                    return

            task_id = DeepCollectRepository.create_task(
                warehouse_id=record_id,
                url=url,
                title=record.get("title", ""),
            )
            DeepCollectService.start_async(task_id)
            OperationLogRepository.add(
                self.get_current_user(), "admin", "深度采集",
                f"启动深度采集任务: {record.get('title', '')}", self.request.remote_ip
            )
            self.write_json(data={"task_id": task_id}, msg="深度采集任务已启动")

        elif action == "batch_start":
            record_ids = body.get("record_ids", [])
            if not record_ids:
                self.write_json(1, "请选择要深度采集的数据")
                return

            task_ids = []
            skipped = 0
            for record_id in record_ids:
                record = DataWarehouseRepository.get_record_by_id(int(record_id))
                if not record:
                    continue
                url = record.get("url", "")
                if not url:
                    skipped += 1
                    continue

                existing_tasks = DeepCollectRepository.get_tasks_by_warehouse(int(record_id))
                has_active = any(t["status"] in ("pending", "running") for t in existing_tasks)
                if has_active:
                    skipped += 1
                    continue

                task_id = DeepCollectRepository.create_task(
                    warehouse_id=int(record_id),
                    url=url,
                    title=record.get("title", ""),
                )
                DeepCollectService.start_async(task_id)
                task_ids.append(task_id)

            OperationLogRepository.add(
                self.get_current_user(), "admin", "批量深度采集",
                f"批量启动{len(task_ids)}个深度采集任务", self.request.remote_ip
            )
            self.write_json(data={"task_ids": task_ids, "skipped": skipped},
                          msg=f"已启动 {len(task_ids)} 个任务，跳过 {skipped} 个")

        elif action == "delete":
            task_id = int(body.get("task_id", 0))
            if not task_id:
                self.write_json(1, "缺少任务ID")
                return
            DeepCollectRepository.delete_task(task_id)
            self.write_json(msg="删除成功")
