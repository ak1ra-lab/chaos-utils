from unittest.mock import mock_open, patch

import httpx
import pytest

from chaos_utils.wechat import (
    WechatWorkApp,
    WechatWorkBot,
    WechatWorkBotFileTooLarge,
    WechatWorkBotFileTooSmall,
)


# WechatWorkApp Tests
class TestWechatWorkApp:
    @pytest.fixture
    def app(self):
        with patch("httpx.get") as mock_get:
            mock_get.return_value.json.return_value = {
                "errcode": 0,
                "access_token": "test_token",
            }
            return WechatWorkApp("test_corpid", "test_secret", "test_agentid")

    def test_init(self):
        app = WechatWorkApp("id", "secret", "agent")
        assert app.corpid == "id"
        assert app.corpsecret == "secret"
        assert app.agentid == "agent"
        assert app.qyapi == "https://qyapi.weixin.qq.com/cgi-bin"

    def test_get_token(self, app):
        with patch("httpx.get") as mock_get:
            mock_get.return_value.json.return_value = {
                "errcode": 0,
                "access_token": "new_token",
            }
            token = app.get_token()
            assert token == "new_token"
            mock_get.assert_called_once_with(
                "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
                params={"corpid": "test_corpid", "corpsecret": "test_secret"},
            )

    def test_send_text(self, app):
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = app.send_text("test message")
            assert resp["errcode"] == 0
            mock_post.assert_called_once_with(
                "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                params={"access_token": "test_token"},
                json={
                    "touser": "@all",
                    "msgtype": "text",
                    "agentid": "test_agentid",
                    "text": {"content": "test message"},
                    "safe": 0,
                },
            )

    def test_get_token_http_error(self, app):
        with patch("httpx.get", side_effect=httpx.RequestError("timeout")):
            token = app.get_token()
        assert token is None

    def test_get_token_json_error(self, app):
        with patch("httpx.get") as mock_get:
            mock_get.return_value.json.side_effect = ValueError("bad json")
            token = app.get_token()
        assert token is None

    def test_get_token_api_error(self, app):
        with patch("httpx.get") as mock_get:
            mock_get.return_value.json.return_value = {
                "errcode": 40001,
                "errmsg": "invalid credential",
            }
            token = app.get_token()
        assert token is None

    def test_send_text_http_error(self, app):
        with patch("httpx.post", side_effect=httpx.RequestError("conn refused")):
            resp = app.send_text("hello")
        assert resp["errcode"] == -1

    def test_send_text_json_error(self, app):
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.side_effect = ValueError("not json")
            resp = app.send_text("hello")
        assert resp["errcode"] == -1


# WechatWorkBot Tests
class TestWechatWorkBot:
    @pytest.fixture
    def bot(self):
        return WechatWorkBot("test_key")

    def test_init(self, bot):
        assert bot.key == "test_key"
        assert bot.qyapi == "https://qyapi.weixin.qq.com/cgi-bin"
        assert bot.send_url == f"{bot.qyapi}/webhook/send?key=test_key"
        assert (
            bot.upload_media_url
            == f"{bot.qyapi}/webhook/upload_media?type=file&key=test_key"
        )

    def test_send_text(self, bot):
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = bot.send_text("test message")
            assert resp["errcode"] == 0

    def test_send_markdown(self, bot):
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = bot.send_markdown("**test**")
            assert resp["errcode"] == 0

    def test_send_image_url(self, bot):
        with patch("httpx.get") as mock_get, patch("httpx.post") as mock_post:
            mock_get.return_value.content = b"fake_image_data"
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = bot.send_image("http://example.com/image.jpg")
            assert resp["errcode"] == 0

    def test_send_image_file(self, bot):
        mock_data = b"fake_image_data"
        m = mock_open(read_data=mock_data)
        with patch("builtins.open", m), patch("httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = bot.send_image("image.jpg")
            assert resp["errcode"] == 0

    def test_send_image_too_large(self, bot):
        large_data = b"x" * (2 * 2**20 + 1)  # Larger than 2MB
        m = mock_open(read_data=large_data)
        with patch("builtins.open", m):
            with pytest.raises(WechatWorkBotFileTooLarge):
                bot.send_image("large.jpg")

    def test_send_news(self, bot):
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = bot.send_news(
                "title", "desc", "http://example.com", "http://example.com/pic.jpg"
            )
            assert resp["errcode"] == 0

    def test_send_news_multiple(self, bot):
        articles = [
            {
                "title": "title1",
                "description": "desc1",
                "url": "http://example.com/1",
                "picurl": "http://example.com/pic1.jpg",
            }
        ]
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = bot.send_news_multiple(articles)
            assert resp["errcode"] == 0

    def test_upload_media(self, bot):
        mock_data = b"x" * 1000  # Valid size between 5B and 20MB
        m = mock_open(read_data=mock_data)
        with patch("builtins.open", m), patch("httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "errcode": 0,
                "media_id": "test_media_id",
            }
            media_id = bot.upload_media("test.txt")
            assert media_id == "test_media_id"

    def test_upload_media_too_small(self, bot):
        mock_data = b"x" * 4  # Smaller than 5B
        m = mock_open(read_data=mock_data)
        with patch("builtins.open", m):
            with pytest.raises(WechatWorkBotFileTooSmall):
                bot.upload_media("small.txt")

    def test_upload_media_too_large(self, bot):
        with patch("builtins.open") as mock_file:
            mock_file.return_value.__enter__.return_value.read.side_effect = [
                b"x" * (20 * 2**20),  # First read returns max size
                b"x",  # Second read returns extra byte
            ]
            with pytest.raises(WechatWorkBotFileTooLarge):
                bot.upload_media("large.txt")

    def test_send_file(self, bot):
        with (
            patch.object(bot, "upload_media") as mock_upload,
            patch("httpx.post") as mock_post,
        ):
            mock_upload.return_value = "test_media_id"
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = bot.send_file("test.txt")
            assert resp["errcode"] == 0
            mock_upload.assert_called_once_with("test.txt")

    def test_send_image_url_unexpected_error(self, bot):
        """Non-RequestError exception during image fetch is caught and re-raised."""
        with patch("httpx.get", side_effect=RuntimeError("unexpected")):
            with pytest.raises(RuntimeError, match="unexpected"):
                bot.send_image("http://example.com/img.jpg")

    # ------------------------------------------------------------------
    # Error / exception paths
    # ------------------------------------------------------------------

    def test_send_text_http_error(self, bot):
        with patch("httpx.post", side_effect=httpx.RequestError("conn")):
            resp = bot.send_text("hi")
        assert resp["errcode"] == -1

    def test_send_text_json_error(self, bot):
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.side_effect = ValueError("bad")
            resp = bot.send_text("hi")
        assert resp["errcode"] == -1

    def test_send_markdown_http_error(self, bot):
        with patch("httpx.post", side_effect=httpx.RequestError("conn")):
            resp = bot.send_markdown("**text**")
        assert resp["errcode"] == -1

    def test_send_markdown_json_error(self, bot):
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.side_effect = ValueError("bad")
            resp = bot.send_markdown("**text**")
        assert resp["errcode"] == -1

    def test_send_image_url_http_fetch_error(self, bot):
        with patch("httpx.get", side_effect=httpx.RequestError("fetch fail")):
            with pytest.raises(httpx.RequestError):
                bot.send_image("http://example.com/img.jpg")

    def test_send_image_url_too_large(self, bot):
        large_bytes = b"x" * (2 * 2**20 + 1)
        with patch("httpx.get") as mock_get:
            mock_get.return_value.content = large_bytes
            with pytest.raises(WechatWorkBotFileTooLarge):
                bot.send_image("http://example.com/big.jpg")

    def test_send_image_file_oserror(self, bot):
        with patch("builtins.open", side_effect=OSError("no such file")):
            with pytest.raises(OSError):
                bot.send_image("nonexistent.jpg")

    def test_send_image_post_http_error(self, bot):
        mock_data = b"valid_image"
        m = mock_open(read_data=mock_data)
        with (
            patch("builtins.open", m),
            patch("httpx.post", side_effect=httpx.RequestError("post fail")),
        ):
            resp = bot.send_image("img.jpg")
        assert resp["errcode"] == -1

    def test_send_image_post_json_error(self, bot):
        mock_data = b"valid_image"
        m = mock_open(read_data=mock_data)
        with patch("builtins.open", m), patch("httpx.post") as mock_post:
            mock_post.return_value.json.side_effect = ValueError("bad json")
            resp = bot.send_image("img.jpg")
        assert resp["errcode"] == -1

    def test_send_news_http_error(self, bot):
        with patch("httpx.post", side_effect=httpx.RequestError("conn")):
            resp = bot.send_news("t", "d", "http://u", "http://p")
        assert resp["errcode"] == -1

    def test_send_news_json_error(self, bot):
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.side_effect = ValueError("bad")
            resp = bot.send_news("t", "d", "http://u", "http://p")
        assert resp["errcode"] == -1

    def test_send_news_multiple_http_error(self, bot):
        with patch("httpx.post", side_effect=httpx.RequestError("conn")):
            resp = bot.send_news_multiple([])
        assert resp["errcode"] == -1

    def test_send_news_multiple_json_error(self, bot):
        with patch("httpx.post") as mock_post:
            mock_post.return_value.json.side_effect = ValueError("bad")
            resp = bot.send_news_multiple([])
        assert resp["errcode"] == -1

    def test_send_file_oserror(self, bot):
        with patch.object(bot, "upload_media", side_effect=OSError("no file")):
            resp = bot.send_file("missing.txt")
        assert resp["errcode"] == -1

    def test_send_file_json_error(self, bot):
        with (
            patch.object(bot, "upload_media", return_value="mid"),
            patch("httpx.post") as mock_post,
        ):
            mock_post.return_value.json.side_effect = ValueError("bad")
            resp = bot.send_file("f.txt")
        assert resp["errcode"] == -1

    def test_upload_media_oserror(self, bot):
        with patch("builtins.open", side_effect=OSError("no file")):
            with pytest.raises(OSError):
                bot.upload_media("missing.txt")

    def test_upload_media_http_error(self, bot):
        mock_data = b"x" * 100
        m = mock_open(read_data=mock_data)
        with (
            patch("builtins.open", m),
            patch("httpx.post", side_effect=httpx.RequestError("conn")),
        ):
            with pytest.raises(httpx.RequestError):
                bot.upload_media("f.txt")

    def test_upload_media_json_error(self, bot):
        mock_data = b"x" * 100
        m = mock_open(read_data=mock_data)
        with patch("builtins.open", m), patch("httpx.post") as mock_post:
            mock_post.return_value.json.side_effect = ValueError("bad json")
            with pytest.raises(ValueError, match="bad json"):
                bot.upload_media("f.txt")

    def test_upload_media_api_error(self, bot):
        mock_data = b"x" * 100
        m = mock_open(read_data=mock_data)
        with patch("builtins.open", m), patch("httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "errcode": 40005,
                "errmsg": "fail",
            }
            with pytest.raises(Exception, match="Upload media failed"):
                bot.upload_media("f.txt")

    def test_upload_media_missing_media_id(self, bot):
        """errcode==0 but no media_id in response raises ValueError."""
        mock_data = b"x" * 100
        m = mock_open(read_data=mock_data)
        with patch("builtins.open", m), patch("httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {"errcode": 0}
            with pytest.raises(ValueError, match="media_id is missing"):
                bot.upload_media("f.txt")
