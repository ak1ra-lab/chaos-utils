import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Any, Dict, List, Optional

import httpx

from chaos_utils.logging import setup_logger

# Enable logging
logger = setup_logger(__name__)


class DingTalkBot:
    """DingTalk robot for sending messages with signature authentication."""

    def __init__(self, access_token: str, secret: str) -> None:
        """
        Initialize DingTalk robot with access token and secret.
        Args:
            access_token (str): The access token of DingTalk robot
            secret (str): The secret key for signature
        """
        self.access_token = access_token
        self.secret = secret
        self.webhook_url = (
            f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"
        )

    def _generate_signature(self) -> tuple[str, str]:
        """
        Generate signature for the request.
        Returns:
            tuple: (timestamp, signature)
        """
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        try:
            hmac_code = hmac.new(
                self.secret.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
            signature = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            return timestamp, signature
        except Exception as e:
            logger.error("Failed to generate signature: %s", e)
            raise

    def _send_message(
        self,
        msg_type: str,
        content: Dict[str, Any],
        at: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send message to DingTalk group.
        Args:
            msg_type (str): Message type ('text', 'markdown', 'link', etc.)
            content (dict): Message content dictionary
            at (dict, optional): At specific users or all users
        Returns:
            dict: API response
        """
        try:
            timestamp, signature = self._generate_signature()
        except Exception as e:
            logger.error("Failed to prepare request: %s", e)
            return {"errcode": -1, "errmsg": str(e)}

        webhook_url = f"{self.webhook_url}&timestamp={timestamp}&sign={signature}"
        data = {"msgtype": msg_type, msg_type: content}
        if at:
            data["at"] = at

        try:
            resp = httpx.post(webhook_url, json=data)
            resp_json = resp.json()
            return resp_json
        except httpx.RequestError as e:
            logger.error("HTTP request failed when sending message: %s", e)
            return {"errcode": -1, "errmsg": str(e)}
        except ValueError as e:
            logger.error("Failed to parse response: %s", e)
            return {"errcode": -1, "errmsg": str(e)}

    def send_text(
        self, content: str, at_mobiles: Optional[List[str]] = None, at_all: bool = False
    ) -> Dict[str, Any]:
        """
        Send text message.
        Args:
            content (str): Text content
            at_mobiles (list, optional): List of mobile numbers to @
            at_all (bool, optional): Whether to @ all members
        Returns:
            dict: API response
        """
        logger.info("Sending text message: %s", content[:100])
        msg_content = {"content": content}
        at = {}
        if at_mobiles:
            at["atMobiles"] = at_mobiles
        if at_all:
            at["isAtAll"] = True

        return self._send_message("text", msg_content, at if at else None)

    def send_markdown(
        self,
        title: str,
        text: str,
        at_mobiles: Optional[List[str]] = None,
        at_all: bool = False,
    ) -> Dict[str, Any]:
        """
        Send markdown message.
        Args:
            title (str): Message title
            text (str): Markdown content
            at_mobiles (list, optional): List of mobile numbers to @
            at_all (bool, optional): Whether to @ all members
        Returns:
            dict: API response
        """
        logger.info("Sending markdown message: %s", title)
        msg_content = {"title": title, "text": text}
        at = {}
        if at_mobiles:
            at["atMobiles"] = at_mobiles
        if at_all:
            at["isAtAll"] = True

        return self._send_message("markdown", msg_content, at if at else None)
