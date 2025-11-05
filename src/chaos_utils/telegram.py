from typing import Any, Dict, Optional, Union

import httpx


class TelegramBot:
    """
    Simple Telegram Bot client for sending messages via the Bot API.

    Parameters:
      token: Bot token like "123456:ABC-DEF..."
      default_chat_id: optional default chat_id (used if chat_id is not provided on send)
      timeout: HTTP request timeout in seconds (float)
    """

    def __init__(
        self,
        token: str,
        default_chat_id: Optional[Union[int, str]] = None,
        timeout: float = 5.0,
    ):
        if not token:
            raise ValueError("token is required")
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.default_chat_id = default_chat_id
        self.timeout = timeout

    def _resolve_chat_id(self, chat_id: Optional[Union[int, str]]) -> Union[int, str]:
        cid = chat_id if chat_id is not None else self.default_chat_id
        if cid is None:
            raise ValueError(
                "chat_id is required (either pass chat_id or set default_chat_id)"
            )
        return cid

    def send_message(
        self,
        text: str,
        chat_id: Optional[Union[int, str]] = None,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
        reply_markup: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Send a text message using sendMessage.

        Parameters:
          text: message text to send
          chat_id: target chat_id (if not provided, default_chat_id must be set)
          parse_mode: "Markdown" or "HTML" (optional)
          disable_web_page_preview: disable link previews
          disable_notification: send silently
          reply_markup: Telegram reply_markup (keyboard, inline keyboard, etc.) as dict
          timeout: override instance timeout for this request

        Returns:
          Parsed JSON response from Telegram API (dict)

        Exceptions:
          httpx.RequestError / ValueError / RuntimeError
        """
        cid = self._resolve_chat_id(chat_id)
        payload: Dict[str, Any] = {
            "chat_id": cid,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        url = f"{self.base_url}/sendMessage"
        try:
            resp = httpx.post(
                url,
                json=payload,
                timeout=(timeout if timeout is not None else self.timeout),
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                # API returned an error payload
                raise RuntimeError(f"telegram error: {data}")
            return data
        except httpx.RequestError:
            # Propagate httpx request/network errors to caller
            raise

    # Convenience alias
    def send(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Convenience alias, same as send_message.
        """
        return self.send_message(text, **kwargs)
