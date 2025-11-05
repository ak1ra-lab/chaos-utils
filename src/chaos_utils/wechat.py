import base64
import hashlib
import os
from typing import Any, Dict, List, Optional

import httpx

from chaos_utils.logging import setup_logger

# Enable logging
logger = setup_logger(__name__)


class WechatWorkBotFileTooSmall(Exception):
    """Exception raised when file is too small to upload."""

    pass


class WechatWorkBotFileTooLarge(Exception):
    """Exception raised when file is too large to upload/send."""

    pass


class WechatWorkApp:
    """
    Simple wrapper for several WeChat Work API endpoints.
    """

    def __init__(self, corpid: str, corpsecret: str, agentid: str) -> None:
        """
        Initialize WechatWorkApp instance.
        """
        self.qyapi = "https://qyapi.weixin.qq.com/cgi-bin"
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agentid = agentid

        self.token = self.get_token()

    def get_token(self) -> Optional[str]:
        """
        Get access token from WeChat Work API.
        Returns:
            str: access_token if successful, None otherwise.
        """
        url = f"{self.qyapi}/gettoken"
        params = {"corpid": self.corpid, "corpsecret": self.corpsecret}
        try:
            resp = httpx.get(url, params=params)
            resp_json = resp.json()
        except httpx.RequestError as e:
            logger.error("HTTP request failed when getting token: %s", e)
            return None
        except ValueError as e:
            logger.error("Failed to parse token response: %s", e)
            return None

        if resp_json.get("errcode") == 0:
            return resp_json.get("access_token")
        else:
            logger.error("Get token failed: %s", resp_json)
            return None

    def send_text(self, message: str, touser: str = "@all") -> Dict[str, Any]:
        """
        Send a text message to specified user(s).
        Args:
            message (str): Message content.
            touser (str): User(s) to send to, default '@all'.
        Returns:
            dict: API response.
        """
        url = f"{self.qyapi}/message/send"
        params = {"access_token": self.token}
        data = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.agentid,
            "text": {"content": message},
            "safe": 0,
        }
        logger.info(
            "Message: '%s' will be sent to %s by %s", message, touser, self.agentid
        )
        try:
            resp = httpx.post(url, params=params, json=data)
            resp_json = resp.json()
            return resp_json
        except httpx.RequestError as e:
            logger.error("HTTP request failed when sending text: %s", e)
            return {"errcode": -1, "errmsg": str(e)}
        except ValueError as e:
            logger.error("Failed to parse send_text response: %s", e)
            return {"errcode": -1, "errmsg": str(e)}


class WechatWorkBot:
    """
    WeChat Work Bot for sending messages and files via webhook.
    """

    def __init__(self, key: str) -> None:
        """
        Initialize WechatWorkBot instance.
        Args:
            key (str): webhook key.
        """
        self.key = key
        self.qyapi = "https://qyapi.weixin.qq.com/cgi-bin"
        self.send_url = f"{self.qyapi}/webhook/send?key={self.key}"
        self.upload_media_url = (
            f"{self.qyapi}/webhook/upload_media?type=file&key={self.key}"
        )

        # Image (before base64 encoding) must not exceed 2MB, supports JPG, PNG format
        self.imagesize_max = 2 * 2**20

        # upload_media requires file size between 5B and 20MB
        self.filesize_min = 5
        self.filesize_max = 20 * 2**20

    def send_text(
        self,
        message: str,
        mentioned_list: Optional[List[str]] = None,
        mentioned_mobile_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a text message.
        Args:
            message (str): Message content.
            mentioned_list (list): List of mentioned users.
            mentioned_mobile_list (list): List of mentioned mobile numbers.
        Returns:
            dict: API response.
        """
        if mentioned_list is None:
            mentioned_list = []
        if mentioned_mobile_list is None:
            mentioned_mobile_list = []
        data = {
            "msgtype": "text",
            "text": {
                "content": message,
                "mentioned_list": mentioned_list,
                "mentioned_mobile_list": mentioned_mobile_list,
            },
        }

        try:
            resp = httpx.post(self.send_url, json=data)
            resp_json = resp.json()
            return resp_json
        except httpx.RequestError as e:
            logger.error("HTTP request failed when sending bot text: %s", e)
            return {"errcode": -1, "errmsg": str(e)}
        except ValueError as e:
            logger.error("Failed to parse bot send_text response: %s", e)
            return {"errcode": -1, "errmsg": str(e)}

    def send_markdown(self, message: str) -> Dict[str, Any]:
        """
        Send a markdown message.
        Args:
            message (str): Markdown content.
        Returns:
            dict: API response.
        """
        data = {"msgtype": "markdown", "markdown": {"content": message}}

        try:
            resp = httpx.post(self.send_url, json=data)
            resp_json = resp.json()
            return resp_json
        except httpx.RequestError as e:
            logger.error("HTTP request failed when sending markdown: %s", e)
            return {"errcode": -1, "errmsg": str(e)}
        except ValueError as e:
            logger.error("Failed to parse markdown response: %s", e)
            return {"errcode": -1, "errmsg": str(e)}

    def send_image(self, image_uri: str) -> Dict[str, Any]:
        """
        Send an image message.
        Args:
            image_uri (str): Image file path or URL.
        Returns:
            dict: API response.
        Raises:
            WechatWorkBotFileTooLarge: If image is too large.
        """
        if image_uri.startswith("http"):
            try:
                resp = httpx.get(image_uri)
                image_bytes = resp.content
            except httpx.RequestError as e:
                logger.error("HTTP request failed when fetching image: %s", e)
                raise
            except Exception as e:
                logger.error("Unexpected error when fetching image: %s", e)
                raise
            if len(image_bytes) > self.imagesize_max:
                raise WechatWorkBotFileTooLarge(
                    "Image %s too large to send" % image_uri
                )
        else:
            try:
                with open(image_uri, mode="rb") as f:
                    image_bytes = f.read(self.imagesize_max)
                    if f.read(1):
                        raise WechatWorkBotFileTooLarge(
                            "Image %s too large to send" % image_uri
                        )
            except OSError as e:
                logger.error("Failed to open image file: %s", e)
                raise

        data = {
            "msgtype": "image",
            "image": {
                "base64": base64.b64encode(image_bytes).decode(),
                "md5": hashlib.md5(image_bytes).hexdigest(),
            },
        }

        try:
            resp = httpx.post(self.send_url, json=data)
            resp_json = resp.json()
            return resp_json
        except httpx.RequestError as e:
            logger.error("HTTP request failed when sending image: %s", e)
            return {"errcode": -1, "errmsg": str(e)}
        except ValueError as e:
            logger.error("Failed to parse image response: %s", e)
            return {"errcode": -1, "errmsg": str(e)}

    def send_news(
        self, title: str, description: str, url: str, picurl: str
    ) -> Dict[str, Any]:
        """
        Send a single news article.
        Args:
            title (str): Article title.
            description (str): Article description.
            url (str): Article URL.
            picurl (str): Article picture URL.
        Returns:
            dict: API response.
        """
        data = {
            "msgtype": "news",
            "news": {
                "articles": [
                    {
                        "title": title,
                        "description": description,
                        "url": url,
                        "picurl": picurl,
                    }
                ]
            },
        }
        try:
            resp = httpx.post(self.send_url, json=data)
            resp_json = resp.json()
            return resp_json
        except httpx.RequestError as e:
            logger.error("HTTP request failed when sending news: %s", e)
            return {"errcode": -1, "errmsg": str(e)}
        except ValueError as e:
            logger.error("Failed to parse news response: %s", e)
            return {"errcode": -1, "errmsg": str(e)}

    def send_news_multiple(self, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Send multiple news articles.
        Args:
            articles (list): List of article dicts.
        Returns:
            dict: API response.
        """
        data = {"msgtype": "news", "news": {"articles": articles}}
        try:
            resp = httpx.post(self.send_url, json=data)
            resp_json = resp.json()
            return resp_json
        except httpx.RequestError as e:
            logger.error("HTTP request failed when sending multiple news: %s", e)
            return {"errcode": -1, "errmsg": str(e)}
        except ValueError as e:
            logger.error("Failed to parse multiple news response: %s", e)
            return {"errcode": -1, "errmsg": str(e)}

    def send_file(self, filename: str) -> Dict[str, Any]:
        """
        Send a file message.
        Args:
            filename (str): File path.
        Returns:
            dict: API response.
        """
        try:
            media_id = self.upload_media(filename)
            data = {"msgtype": "file", "file": {"media_id": media_id}}
            resp = httpx.post(self.send_url, json=data)
            resp_json = resp.json()
            return resp_json
        except (httpx.RequestError, OSError) as e:
            logger.error("Failed to send file: %s", e)
            return {"errcode": -1, "errmsg": str(e)}
        except ValueError as e:
            logger.error("Failed to parse file response: %s", e)
            return {"errcode": -1, "errmsg": str(e)}

    def upload_media(self, filename: str) -> str:
        """
        Upload a file to WeChat Work webhook.
        Args:
            filename (str): File path.
        Returns:
            str: media_id if successful.
        Raises:
            WechatWorkBotFileTooLarge: If file is too large.
            WechatWorkBotFileTooSmall: If file is too small.
        """
        try:
            with open(filename, "rb") as f:
                content = f.read(self.filesize_max)
                if f.read(1):
                    raise WechatWorkBotFileTooLarge(
                        "File %s too large to upload" % filename
                    )
                elif len(content) < self.filesize_min:
                    raise WechatWorkBotFileTooSmall(
                        "File %s too small to upload" % filename
                    )
        except OSError as e:
            logger.error("Failed to open file for upload: %s", e)
            raise

        files = {"media": (os.path.basename(filename), content)}
        try:
            resp = httpx.post(self.upload_media_url, files=files)
            resp_json = resp.json()
        except httpx.RequestError as e:
            logger.error("HTTP request failed when uploading media: %s", e)
            raise
        except ValueError as e:
            logger.error("Failed to parse upload media response: %s", e)
            raise

        if resp_json.get("errcode") == 0:
            return resp_json.get("media_id")
        else:
            logger.error("Upload media failed: %s", resp_json)
            raise Exception("Upload media failed: %s" % resp_json)
