import json
import re
import tornado.web
import tornado.websocket
from concurrent.futures import ThreadPoolExecutor

from app.controllers.base import BaseHandler
from app.models.model import AIModelRepository, AIModelService
from app.models.digital_employee import DigitalEmployeeRepository, DigitalEmployeeService
from app.models.conversation import ConversationRepository, ChatMessageRepository
from app.models.user import UserRepository


class ChatHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = self.current_user
        self.render("chat.html", title="智能瞭望与问数系统", username=username)


class ChatWebSocketHandler(BaseHandler, tornado.websocket.WebSocketHandler):

    _executor = ThreadPoolExecutor(max_workers=8)

    def open(self):
        username = self.get_current_user()
        if not username:
            self.close(code=401, reason="unauthorized")
            return
        self.username = username
        user_row = UserRepository.get_user_by_username(username)
        self.user_id = user_row["id"] if user_row else None

    def on_message(self, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            self.write_message({"type": "error", "content": "无效的消息格式"})
            return

        msg_type = data.get("type", "")
        if msg_type == "message":
            content = data.get("content", "")
            conv_id = data.get("conversation_id")
            model_id = data.get("model_id")
            self.handle_message(content, conv_id, model_id)
        elif msg_type == "cancel":
            self._cancelled = True
        elif msg_type == "ping":
            self.write_message({"type": "pong"})

    def handle_message(self, content, conv_id, model_id):
        if not self.user_id:
            self.write_message({"type": "error", "content": "用户不存在"})
            return

        self._cancelled = False

        # Detect @employee mention
        mention_match = re.match(r'@(\w+)\s+(.*)', content, re.DOTALL)
        if mention_match:
            emp_code = mention_match.group(1)
            user_message = mention_match.group(2) or content
            self._handle_employee(emp_code, user_message, conv_id)
        else:
            self._handle_ai_chat(content, conv_id, model_id)

    def _handle_employee(self, emp_code, user_message, conv_id):
        emp = DigitalEmployeeRepository.get_by_code(emp_code)
        if not emp or emp.get("status") != 1:
            self.write_message({"type": "stream", "content": f"[未找到可用的数字员工: @{emp_code}]\n"})
            self.write_message({"type": "done"})
            return

        if not conv_id:
            conv_id = ConversationRepository.create(self.user_id, f"与 {emp['name']} 对话")

        ChatMessageRepository.add(conv_id, "user", f"@{emp_code} {user_message}")

        self.write_message({"type": "stream", "content": f"正在调度数字员工 **{emp['name']}**...\n\n"})

        try:
            result = DigitalEmployeeService.execute(emp, user_message=user_message)
        except Exception as e:
            self.write_message({"type": "stream", "content": f"\n错误: {str(e)}\n"})
            self.write_message({"type": "done", "conversation_id": conv_id})
            return

        if self._cancelled:
            return

        if result.get("success"):
            content_str = result.get("content", "")
            if isinstance(content_str, list):
                # Article list format
                text_parts = []
                for i, article in enumerate(content_str[:20], 1):
                    if isinstance(article, dict):
                        title = article.get("title", "")
                        url = article.get("url", "")
                        text_parts.append(f"{i}. [{title}]({url})")
                    else:
                        text_parts.append(f"{i}. {article}")
                response_text = "\n".join(text_parts) if text_parts else "未找到相关内容"
                self.write_message({"type": "stream", "content": response_text + "\n"})
            elif isinstance(content_str, dict):
                response_text = json.dumps(content_str, ensure_ascii=False, indent=2)
                self.write_message({"type": "stream", "content": response_text + "\n"})
            else:
                self.write_message({"type": "stream", "content": str(content_str) + "\n"})
        else:
            self.write_message({"type": "stream", "content": f"执行失败: {result.get('error', '未知错误')}\n"})

        ChatMessageRepository.add(conv_id, "assistant",
            str(result.get("content", "")) if not isinstance(result.get("content"), (list, dict))
            else json.dumps(result.get("content", ""), ensure_ascii=False))
        ConversationRepository.touch(conv_id)
        self.write_message({"type": "done", "conversation_id": conv_id})

    def _handle_ai_chat(self, content, conv_id, model_id):
        # Resolve model
        model = None
        if model_id:
            model = AIModelRepository.get_model_by_id(int(model_id))
        if not model:
            model = AIModelRepository.get_default_model()
        if not model:
            self.write_message({"type": "error", "content": "未找到可用的AI模型，请在后台配置模型引擎"})
            return

        if not conv_id:
            conv_id = ConversationRepository.create(self.user_id,
                title="新对话",
                model_name=model.get("name", ""))

        # Save user message
        ChatMessageRepository.add(conv_id, "user", content)

        # Build message history
        history = ChatMessageRepository.get_by_conversation(conv_id)
        messages = []
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})

        self._cancelled = False
        full_response = ""

        try:
            # Run blocking HTTP call in thread pool
            future = self._executor.submit(
                AIModelService.chat_completion_sync, model, messages
            )
            # We need streaming, but chat_completion_sync is non-streaming.
            # For streaming we need to call the generator from a thread — instead,
            # let's use the sync version and stream the final result as chunks.
            result = future.result(timeout=120)

            if self._cancelled:
                return

            if "choices" in result and result["choices"]:
                choice = result["choices"][0]
                full_response = choice["message"]["content"]
                # Stream the response character by chunk for a natural feel
                chunk_size = 10
                for i in range(0, len(full_response), chunk_size):
                    if self._cancelled:
                        break
                    chunk = full_response[i:i + chunk_size]
                    self.write_message({"type": "stream", "content": chunk})
                self.write_message({"type": "stream", "content": "\n"})

                # Update token counts
                usage = result.get("usage", {})
                if usage:
                    AIModelRepository.update_tokens(
                        model["id"],
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0)
                    )
            else:
                self.write_message({"type": "stream", "content": "[模型无响应]\n"})
        except Exception as e:
            self.write_message({"type": "stream", "content": f"\n[错误: {str(e)}]\n"})

        # Save assistant response
        if full_response:
            ChatMessageRepository.add(conv_id, "assistant", full_response)

        # Auto-generate title from first AI response
        conv = ConversationRepository.get_by_id(conv_id)
        if conv and (not conv.get("title") or conv["title"] == "新对话"):
            title = self._generate_title(content)
            ConversationRepository.update_title(conv_id, title)

        ConversationRepository.touch(conv_id)
        self.write_message({"type": "done", "conversation_id": conv_id,
                          "title": self._generate_title(content)})

    def _generate_title(self, content):
        title = content.strip()[:30]
        if len(content) > 30:
            title += "..."
        return title

    def on_close(self):
        self._cancelled = True

    def check_origin(self, origin):
        return True
