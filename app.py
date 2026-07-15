import os
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer

from app.controllers.auth import LoginHandler, LogoutHandler, RegisterHandler
from app.controllers.home import IndexHandler
from app.controllers.chat import ChatHandler, ChatWebSocketHandler
from app.controllers.report import ReportHandler
from app.controllers.history import HistoryHandler
from app.controllers.export import ExportHandler
from app.controllers.api import (
    UserModelsAPIHandler, UserEmployeesAPIHandler,
    UserConversationsAPIHandler, UserConversationAPIHandler,
)
from app.controllers.admin import (
    AdminLoginHandler, AdminLogoutHandler, AdminIndexHandler,
    AdminUserHandler, AdminFunctionHandler, AdminMenuHandler,
    AdminRoleHandler, AdminWatchHandler, AdminDataHandler,
    AdminCollectionHandler, AdminDigitalEmployeeHandler,
    AdminModelHandler, AdminDashboardHandler, AdminSentimentHandler,
    AdminWarehousePageHandler,
    AdminDeepCollectAPIHandler,
    AdminUserAPIHandler, AdminRoleAPIHandler,
    AdminFunctionAPIHandler, AdminMenuAPIHandler,
    AdminTreeDataHandler,
    AdminWatchSourceAPIHandler, AdminWatchTaskAPIHandler,
    AdminWatchResultAPIHandler, AdminLogAPIHandler,
    AdminModelAPIHandler, AdminModelTestHandler,
    AdminWarehouseAPIHandler,
    AdminDigitalEmployeeAPIHandler,
    AdminDeepCollectAPIHandler,
)
from app.models.db import init_db


def webapp():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    settings = dict(
        template_path=os.path.join(base_dir, "app", "templates"),
        static_path=os.path.join(base_dir, "app", "static"),
        cookie_secret="datafinder-token-2025-secure",
        login_url="/",
        xsrf_cookies=True,
        debug=True,
        autoreload=True,
    )
    return tornado.web.Application([
        # ========== 用户侧（前台）路由 ==========
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

        # ========== 用户侧（前台）API 路由 ==========
        (r"/api/models", UserModelsAPIHandler),
        (r"/api/employees", UserEmployeesAPIHandler),
        (r"/api/conversations", UserConversationsAPIHandler),
        (r"/api/conversations/(\d+)", UserConversationAPIHandler),

        # ========== 管理侧（后台）页面路由 ==========
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
        (r"/admin/warehouse", AdminWarehousePageHandler),

        # ========== 管理侧（后台）API 路由 ==========
        (r"/admin/api/users", AdminUserAPIHandler),
        (r"/admin/api/roles", AdminRoleAPIHandler),
        (r"/admin/api/functions", AdminFunctionAPIHandler),
        (r"/admin/api/menus", AdminMenuAPIHandler),
        (r"/admin/api/treedata", AdminTreeDataHandler),

        # ========== 瞭望系统 API 路由 ==========
        (r"/admin/api/watch/sources", AdminWatchSourceAPIHandler),
        (r"/admin/api/watch/tasks", AdminWatchTaskAPIHandler),
        (r"/admin/api/watch/results", AdminWatchResultAPIHandler),

        # ========== 操作日志 API 路由 ==========
        (r"/admin/api/logs", AdminLogAPIHandler),

        # ========== AI 模型引擎 API 路由 ==========
        (r"/admin/api/models", AdminModelAPIHandler),
        (r"/admin/api/model/test", AdminModelTestHandler),

        # ========== 数字员工 API 路由 ==========
        (r"/admin/api/digital_employees", AdminDigitalEmployeeAPIHandler),

        # ========== 数据仓库 API 路由 ==========
        (r"/admin/api/warehouse", AdminWarehouseAPIHandler),

        # ========== 深度采集 API 路由 ==========
        (r"/admin/api/deep_collect", AdminDeepCollectAPIHandler),
    ],
        **settings
    )


if __name__ == '__main__':
    init_db()
    webapp = webapp()
    server = HTTPServer(webapp)
    server.listen(10010)
    print("Server Started: http://localhost:10010/", flush=True)
    print("Admin Panel: http://localhost:10010/admin/login", flush=True)
    tornado.ioloop.IOLoop.current().start()
