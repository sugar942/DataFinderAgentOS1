import tornado.web
from app.controllers.base import BaseHandler

class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("chat.html",title="智能瞭望与问数系统",username=self.current_user)
