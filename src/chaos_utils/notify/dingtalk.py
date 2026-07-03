"""DingTalk custom bot for sending messages via webhook.

Webhook URL format:
    https://oapi.dingtalk.com/robot/send?access_token=<ACCESS_TOKEN>

Signature: HMAC-SHA256 using secret as key, ``timestamp + "\\n" + secret``
as message, then Base64-encode and URL-encode the result.

Documentation:
    https://open.dingtalk.com/document/development/robot-message-type
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
import urllib.parse
from typing import Any

import httpx2

from chaos_utils.notify.base import BaseNotifier

logger = logging.getLogger(__name__)


class DingTalkBot(BaseNotifier):
    """DingTalk custom bot for sending messages via webhook.

    Parameters:
        access_token: The access token from the DingTalk bot webhook URL.
        secret: Optional signing secret.  When provided every request is
            signed with HMAC-SHA256.
    """

    def __init__(self, access_token: str, secret: str = "") -> None:
        self.access_token = access_token
        self.secret = secret
        self.webhook_url = (
            f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"
        )

    def send(self, text: str) -> bool:
        try:
            self.send_text(text)
        except Exception:
            logger.exception("DingTalk send() failed")
            return False
        return True

    def send_text(
        self,
        content: str,
        at_mobiles: list[str] | None = None,
        at_all: bool = False,
    ) -> dict[str, Any]:
        logger.info("Sending DingTalk text message: %s", content[:100])
        msg_content: dict[str, Any] = {"content": content}
        at = self._build_at(at_mobiles, at_all)
        return self._send_message("text", msg_content, at)

    def send_markdown(
        self,
        title: str,
        text: str,
        at_mobiles: list[str] | None = None,
        at_all: bool = False,
    ) -> dict[str, Any]:
        logger.info("Sending DingTalk markdown message: %s", title)
        msg_content: dict[str, Any] = {"title": title, "text": text}
        at = self._build_at(at_mobiles, at_all)
        return self._send_message("markdown", msg_content, at)

    @staticmethod
    def _build_at(at_mobiles: list[str] | None, at_all: bool) -> dict[str, Any] | None:
        at: dict[str, Any] = {}
        if at_mobiles:
            at["atMobiles"] = at_mobiles
        if at_all:
            at["isAtAll"] = True
        return at if at else None

    def _generate_signature(self) -> tuple[str, str]:
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, signature

    def _send_message(
        self,
        msg_type: str,
        content: dict[str, Any],
        at: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = self.webhook_url
        if self.secret:
            timestamp, signature = self._generate_signature()
            url = f"{url}&timestamp={timestamp}&sign={signature}"

        data: dict[str, Any] = {"msgtype": msg_type, msg_type: content}
        if at:
            data["at"] = at

        resp = httpx2.post(url, json=data)
        resp.raise_for_status()
        return resp.json()
