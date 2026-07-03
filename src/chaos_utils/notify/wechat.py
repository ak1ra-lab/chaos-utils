"""WeChat Work bot for sending messages via webhook.

Webhook URL format:
    https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=<KEY>

Documentation:
    https://developer.work.weixin.qq.com/document/path/91770
"""

from __future__ import annotations

import logging
from typing import Any

import httpx2

from chaos_utils.notify.base import BaseNotifier

logger = logging.getLogger(__name__)


class WechatWorkBot(BaseNotifier):
    """WeChat Work bot for sending messages via webhook.

    Parameters:
        key: The webhook key (the ``key`` query parameter in the webhook URL).
    """

    def __init__(self, key: str) -> None:
        self.key = key
        self.send_url = (
            f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.key}"
        )

    def send(self, text: str) -> bool:
        try:
            self.send_text(text)
        except Exception:
            logger.exception("WechatWorkBot send() failed")
            return False
        return True

    def send_text(
        self,
        message: str,
        mentioned_list: list[str] | None = None,
        mentioned_mobile_list: list[str] | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "msgtype": "text",
            "text": {
                "content": message,
                "mentioned_list": mentioned_list or [],
                "mentioned_mobile_list": mentioned_mobile_list or [],
            },
        }
        resp = httpx2.post(self.send_url, json=data)
        resp.raise_for_status()
        return resp.json()

    def send_markdown_v2(self, message: str) -> dict[str, Any]:
        data: dict[str, Any] = {
            "msgtype": "markdown_v2",
            "markdown_v2": {"content": message},
        }
        resp = httpx2.post(self.send_url, json=data)
        resp.raise_for_status()
        return resp.json()
