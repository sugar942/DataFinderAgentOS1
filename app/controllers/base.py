"""
控制器公共基类 —— BaseHandler
基于 Tornado RequestHandler 扩展：
- 统一提供 get_current_user() 登录态获取逻辑
- 其他业务 Handler 继承此类即可复用会话校验
"""
import tornado.web


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        username = self.get_secure_cookie("username")
        if not username:
            return None
        return username.decode("utf-8")
