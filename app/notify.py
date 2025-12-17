import json
import requests
from .settings import settings


def notify_lark_text(text: str):
    url = getattr(settings, "LARK_WARN_BOT_URL", None)
    if not url:
        return
    try:
        requests.post(url, json={"msg_type": "text", "content": {"text": text}}, timeout=10)
    except Exception:
        pass


def notify_lark_result(task_name: str, payload: dict):
    prefix = settings.APP_NAME
    text = f"[{prefix}] {task_name} ok: {json.dumps(payload, ensure_ascii=False)[:1800]}"
    notify_lark_text(text)


def notify_lark_error(task_name: str, err: Exception):
    prefix = settings.APP_NAME
    text = f"[{prefix}] {task_name} error: {type(err).__name__}: {str(err)}"
    notify_lark_text(text)
