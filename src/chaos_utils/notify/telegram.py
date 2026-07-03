"""Telegram Bot API client for sending messages.

API base URL:
    https://api.telegram.org/bot<TOKEN>

Documentation:
    https://core.telegram.org/bots/api
    Rich Markdown: https://core.telegram.org/bots/api#rich-markdown-style
    Rich HTML: https://core.telegram.org/bots/api#rich-html-style
"""

from __future__ import annotations

import logging
from typing import Any

import httpx2

from chaos_utils.notify.base import BaseNotifier

logger = logging.getLogger(__name__)


class TelegramBot(BaseNotifier):
    """Telegram Bot client for one-way notifications.

    Parameters:
        token: Bot token like ``"123456:ABC-DEF..."``.
        chat_id: Target chat identifier (user, group, or channel).
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        token: str,
        chat_id: int | str,
        timeout: float = 5.0,
    ) -> None:
        if not token:
            raise ValueError("token is required")
        if not chat_id:
            raise ValueError("chat_id is required")
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.chat_id = chat_id
        self.timeout = timeout

    def send(self, text: str) -> bool:
        try:
            self.send_message(text)
        except Exception:
            logger.exception("Telegram send() failed")
            return False
        return True

    def send_message(self, text: str, **kwargs: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text,
        }
        payload.update(kwargs)

        url = f"{self.base_url}/sendMessage"
        resp = httpx2.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"telegram error: {data}")
        return data

    def send_rich_message(
        self,
        html: str | None = None,
        markdown: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a rich formatted message via ``sendRichMessage``.

        Exactly one of *html* or *markdown* must be provided.
        See the `Rich Markdown`_ and `Rich HTML`_ docs for syntax.

        .. _Rich Markdown:
            https://core.telegram.org/bots/api#rich-markdown-style
        .. _Rich HTML:
            https://core.telegram.org/bots/api#rich-html-style
        """
        if (html is None and markdown is None) or (
            html is not None and markdown is not None
        ):
            raise ValueError("exactly one of html or markdown must be provided")

        rich_message: dict[str, Any] = {}
        if html is not None:
            rich_message["html"] = html
        else:
            rich_message["markdown"] = markdown

        payload: dict[str, Any] = {
            "chat_id": self.chat_id,
            "rich_message": rich_message,
        }
        payload.update(kwargs)

        url = f"{self.base_url}/sendRichMessage"
        resp = httpx2.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"telegram error: {data}")
        return data
