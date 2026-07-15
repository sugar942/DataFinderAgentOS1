import json
import tornado.web

from app.controllers.base import BaseHandler
from app.models.model import AIModelRepository
from app.models.digital_employee import DigitalEmployeeRepository
from app.models.conversation import ConversationRepository, ChatMessageRepository
from app.models.user import UserRepository


def _get_user_id(handler):
    username = handler.current_user
    if not username:
        return None
    row = UserRepository.get_user_by_username(username)
    return row["id"] if row else None


class UserModelsAPIHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        rows, _ = AIModelRepository.get_models(page=1, page_size=100)
        models = []
        for r in rows:
            if r.get("status") == 1:
                models.append({
                    "id": r["id"],
                    "name": r["name"],
                    "model_id": r["model_id"],
                    "is_default": r.get("is_default", 0),
                    "provider": r.get("provider", "openai"),
                    "description": r.get("description", ""),
                })
        self.write({"code": 0, "data": models})


class UserEmployeesAPIHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        rows = DigitalEmployeeRepository.get_active()
        employees = []
        for r in rows:
            employees.append({
                "id": r["id"],
                "name": r["name"],
                "code": r["code"],
                "type": r.get("type", "llm"),
                "icon": r.get("icon", "fas fa-robot"),
                "description": r.get("description", ""),
            })
        self.write({"code": 0, "data": employees})


class UserConversationsAPIHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user_id = _get_user_id(self)
        if not user_id:
            self.set_status(401)
            return self.write({"code": -1, "msg": "用户不存在"})
        conversations = ConversationRepository.get_by_user(user_id)
        self.write({"code": 0, "data": [dict(c) for c in conversations]})

    @tornado.web.authenticated
    def post(self):
        user_id = _get_user_id(self)
        if not user_id:
            self.set_status(401)
            return self.write({"code": -1, "msg": "用户不存在"})
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = {}
        title = body.get("title", "新对话")
        model_name = body.get("model_name", "")
        conv_id = ConversationRepository.create(user_id, title, model_name)
        self.write({"code": 0, "data": {"id": conv_id}})


class UserConversationAPIHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, conv_id):
        user_id = _get_user_id(self)
        if not user_id:
            self.set_status(401)
            return self.write({"code": -1, "msg": "用户不存在"})
        conv = ConversationRepository.get_by_id(int(conv_id))
        if not conv or conv["user_id"] != user_id:
            self.set_status(404)
            return self.write({"code": -1, "msg": "对话不存在"})
        action = self.get_argument("action", "")
        if action == "messages":
            messages = ChatMessageRepository.get_by_conversation(int(conv_id))
            return self.write({"code": 0, "data": [dict(m) for m in messages]})
        self.write({"code": 0, "data": dict(conv)})

    @tornado.web.authenticated
    def delete(self, conv_id):
        user_id = _get_user_id(self)
        if not user_id:
            self.set_status(401)
            return self.write({"code": -1, "msg": "用户不存在"})
        conv = ConversationRepository.get_by_id(int(conv_id))
        if not conv or conv["user_id"] != user_id:
            self.set_status(404)
            return self.write({"code": -1, "msg": "对话不存在"})
        ConversationRepository.delete(int(conv_id))
        self.write({"code": 0, "msg": "删除成功"})
