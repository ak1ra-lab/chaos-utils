"""Feishu / Lark custom bot for sending messages via webhook.

Webhook URL format:
    https://open.feishu.cn/open-apis/bot/v2/hook/<HOOK_ID>

Documentation:
    https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from typing import Any

import httpx2

from chaos_utils.notify.base import BaseNotifier

logger = logging.getLogger(__name__)


class FeishuBot(BaseNotifier):
    """Send notifications via Feishu / Lark custom bot webhook.

    Parameters:
        webhook_url: Full webhook URL from the Feishu bot settings.
        secret: Optional signing secret for message verification.
            When set, every request includes a ``timestamp`` and ``sign``
            field computed with HMAC-SHA256 over an empty body using
            ``timestamp + "\\n" + secret`` as the key.
    """

    def __init__(self, webhook_url: str, secret: str = "") -> None:
        self._webhook_url = webhook_url
        self._secret = secret

    def send(self, text: str) -> bool:
        try:
            return self.send_text(text)
        except Exception:
            logger.exception("Feishu send() failed")
            return False

    def send_text(self, text: str) -> bool:
        body: dict[str, Any] = {
            "msg_type": "text",
            "content": {"text": text},
        }
        if self._secret:
            ts, sign = self._sign()
            body["timestamp"] = ts
            body["sign"] = sign
        try:
            resp = httpx2.post(self._webhook_url, json=body)
            resp.raise_for_status()
        except httpx2.HTTPStatusError as exc:
            logger.error(
                "Feishu HTTP %d: %s",
                exc.response.status_code,
                exc.response.text[:200],
            )
            return False
        except httpx2.RequestError as exc:
            logger.error("Feishu request failed: %s", exc)
            return False
        return True

    def _sign(self) -> tuple[str, str]:
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{self._secret}"
        sig = hmac.new(
            string_to_sign.encode("utf-8"),
            b"",
            hashlib.sha256,
        ).digest()
        return timestamp, base64.b64encode(sig).decode("utf-8")
