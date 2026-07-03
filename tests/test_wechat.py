from unittest.mock import patch

import httpx2
import pytest

from chaos_utils.notify.wechat import WechatWorkBot


class TestWechatWorkBot:
    @pytest.fixture
    def bot(self):
        return WechatWorkBot("test_key")

    def test_init(self, bot):
        assert bot.key == "test_key"
        assert (
            bot.send_url
            == "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test_key"
        )

    def test_send_text(self, bot):
        with patch("httpx2.post") as mock_post:
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = bot.send_text("test message")
            assert resp["errcode"] == 0

    def test_send_markdown_v2(self, bot):
        with patch("httpx2.post") as mock_post:
            mock_post.return_value.json.return_value = {"errcode": 0}
            resp = bot.send_markdown_v2("# title\n**bold**")
            assert resp["errcode"] == 0
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert kwargs["json"]["msgtype"] == "markdown_v2"
            assert "markdown_v2" in kwargs["json"]

    def test_send_returns_true_on_success(self, bot):
        with patch.object(bot, "send_text", return_value={"errcode": 0}):
            assert bot.send("hello") is True

    def test_send_returns_false_on_error(self, bot):
        with patch.object(bot, "send_text", side_effect=RuntimeError("fail")):
            assert bot.send("hello") is False

    def test_send_text_http_error(self, bot):
        with patch("httpx2.post", side_effect=httpx2.RequestError("conn")):
            with pytest.raises(httpx2.RequestError, match="conn"):
                bot.send_text("hi")

    def test_send_text_json_error(self, bot):
        with patch("httpx2.post") as mock_post:
            mock_post.return_value.json.side_effect = ValueError("bad")
            with pytest.raises(ValueError, match="bad"):
                bot.send_text("hi")

    def test_send_markdown_v2_http_error(self, bot):
        with patch("httpx2.post", side_effect=httpx2.RequestError("conn")):
            with pytest.raises(httpx2.RequestError, match="conn"):
                bot.send_markdown_v2("# test")
