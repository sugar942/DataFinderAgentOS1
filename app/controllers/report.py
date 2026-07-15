import tornado.web

from app.controllers.base import BaseHandler


class ReportHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = self.current_user
        self.render("report.html", title="数据分析", username=username)