from unittest.mock import mock_open, patch

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
