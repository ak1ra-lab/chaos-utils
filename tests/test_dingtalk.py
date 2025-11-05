from unittest.mock import patch

import pytest

from chaos_utils.dingtalk import DingTalkBot


@pytest.fixture
def bot():
    return DingTalkBot(access_token="test_token", secret="test_secret")


def test_generate_signature_returns_timestamp_and_signature(bot):
    timestamp, signature = bot._generate_signature()
    assert isinstance(timestamp, str)
    assert isinstance(signature, str)
    assert timestamp.isdigit()
    assert len(signature) > 0


@patch("httpx.post")
def test_send_message_text(mock_post, bot):
    mock_post.return_value.json.return_value = {"errcode": 0, "errmsg": "ok"}
    content = {"content": "Hello"}
    resp = bot._send_message("text", content)
    assert resp["errcode"] == 0
    assert resp["errmsg"] == "ok"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "access_token=test_token" in args[0]
    assert kwargs["json"]["msgtype"] == "text"
    assert kwargs["json"]["text"] == content


@patch("httpx.post")
def test_send_message_with_at(mock_post, bot):
    mock_post.return_value.json.return_value = {"errcode": 0}
    content = {"content": "Hi"}
    at = {"atMobiles": ["123456"], "isAtAll": True}
    resp = bot._send_message("text", content, at)
    assert resp["errcode"] == 0
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["at"] == at


@patch("httpx.post")
def test_send_text_with_at_mobiles_and_all(mock_post, bot):
    mock_post.return_value.json.return_value = {"errcode": 0}
    resp = bot.send_text("Hello", at_mobiles=["123456"], at_all=True)
    assert resp["errcode"] == 0
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["at"]["atMobiles"] == ["123456"]
    assert kwargs["json"]["at"]["isAtAll"] is True


@patch("httpx.post")
def test_send_text_without_at(mock_post, bot):
    mock_post.return_value.json.return_value = {"errcode": 0}
    resp = bot.send_text("Hello world")
    assert resp["errcode"] == 0
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "at" not in kwargs["json"]


@patch("httpx.post")
def test_send_markdown_with_at(mock_post, bot):
    mock_post.return_value.json.return_value = {"errcode": 0}
    resp = bot.send_markdown("Title", "Markdown text", at_mobiles=["123"], at_all=True)
    assert resp["errcode"] == 0
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["msgtype"] == "markdown"
    assert kwargs["json"]["markdown"]["title"] == "Title"
    assert kwargs["json"]["markdown"]["text"] == "Markdown text"
    assert kwargs["json"]["at"]["atMobiles"] == ["123"]
    assert kwargs["json"]["at"]["isAtAll"] is True


@patch("httpx.post")
def test_send_markdown_without_at(mock_post, bot):
    mock_post.return_value.json.return_value = {"errcode": 0}
    resp = bot.send_markdown("Title", "Text")
    assert resp["errcode"] == 0
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "at" not in kwargs["json"]
