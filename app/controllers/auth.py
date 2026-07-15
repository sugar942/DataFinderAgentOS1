import tornado.web

from app.controllers.base import BaseHandler
from app.models.user import UserRepository
from app.models.operation_log import OperationLogRepository


class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html",title="用户登录",error=None)

    def post(self):
        username = self.get_body_argument("username","")
        password = self.get_body_argument("password","")
        ip = self.request.remote_ip
        if not username or not password:
            self.set_status(400)
            return self.render("login.html",title="用户登录",error="请输入用户名和密码")

        if not UserRepository.verify_user(username,password):
            OperationLogRepository.add(username, "user", "登录失败", "账号或密码不正确", ip)
            self.set_status(401)
            return self.render("login.html",title="用户登录",error="账号或密码不正确")

        self.set_secure_cookie("username",username)
        OperationLogRepository.add(username, "user", "登录", "用户登录瞭望与问数系统", ip)
        self.redirect("/index")

class LogoutHandler(BaseHandler):
    def post(self):
        username = self.get_secure_cookie("username")
        if username:
            OperationLogRepository.add(
                username.decode("utf-8"), "user", "登出", "用户退出系统",
                self.request.remote_ip
            )
        self.clear_cookie("username")
        self.redirect("/")


class RegisterHandler(BaseHandler):
    def get(self):
        self.render("register.html", title="用户注册", error=None)

    def post(self):
        username = self.get_body_argument("username", "")
        password = self.get_body_argument("password", "")
        confirm_password = self.get_body_argument("confirm_password", "")
        ip = self.request.remote_ip

        if not username or not password:
            self.set_status(400)
            return self.render("register.html", title="用户注册", error="请输入用户名和密码")

        if password != confirm_password:
            self.set_status(400)
            return self.render("register.html", title="用户注册", error="两次输入的密码不一致")

        if not UserRepository.create_user(username, password):
            self.set_status(400)
            return self.render("register.html", title="用户注册", error="该用户名已被使用")

        OperationLogRepository.add(username, "user", "注册", "新用户注册瞭望与问数系统", ip)
        self.redirect("/")
