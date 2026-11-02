"""Production excerpt: private application dependencies are intentionally omitted.

Only the submission method is shown. This is not a standalone Django app.
"""
import json
import uuid
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from compose.models import Conversation, ConversationTurn
from compose.views import ComposeApiLoginRequiredMixin, _compose_disabled

class ConversationDetailView(ComposeApiLoginRequiredMixin, View):
    def post(self, request, pk):
        disabled = _compose_disabled()
        if disabled is not None:
            return disabled
        try:
            body = json.loads(request.body)
            payload = body["payload"]
            request_id = uuid.UUID(str(body["request_id"]))
            if not isinstance(payload, dict) or not isinstance(payload.get("request", {}), dict):
                raise ValueError()
            message = payload.get("message", "")
            if not isinstance(message, str) or not message.strip() or len(message) > 12000:
                raise ValueError()
        except (ValueError, TypeError, KeyError):
            return JsonResponse({"ok": False, "error": "请求格式无效"}, status=400)
        from .tasks import generate_conversation_turn
        with transaction.atomic():
            c = get_object_or_404(Conversation.objects.select_for_update(), pk=pk, user=request.user)
            existing = c.turns.filter(request_id=request_id).first()
            if existing:
                return JsonResponse({"ok": True, "conversation": serialize(c)}, status=202)
            if c.turns.filter(status__in=["queued", "running"]).exists():
                return JsonResponse({"ok": False, "error": "当前对话仍在生成，请等待完成。"}, status=409)
            turn = ConversationTurn.objects.create(conversation=c, request_id=request_id, payload=payload)
            if c.title == "新对话":
                c.title = message[:100]
            c.save()
        try:
            generate_conversation_turn.delay(str(turn.pk))
        except Exception:
            ConversationTurn.objects.filter(pk=turn.pk).update(status="failed", error="后台任务服务暂不可用，请重新发送。")
            return JsonResponse({"ok": False, "error": "后台任务服务暂不可用，请重新发送。"}, status=503)
        return JsonResponse({"ok": True, "conversation": serialize(c)}, status=202)

# serialize() is the private application serializer, omitted from this excerpt.
