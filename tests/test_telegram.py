import httpx2
import pytest

from chaos_utils.notify.telegram import TelegramBot


class FakeResponse:
    """A minimal fake response to emulate httpx2.Response for our tests."""

    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx2.HTTPStatusError("status error", request=None, response=None)

    def json(self):
        return self._json


def test_init_without_token_raises():
    with pytest.raises(ValueError):
        TelegramBot(token="", chat_id=1)


def test_init_without_chat_id_raises():
    with pytest.raises(ValueError):
        TelegramBot(token="t", chat_id="")


def test_send_message_success_and_payload(monkeypatch):
    captured = {}

    def fake_post(url, *args, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse({"ok": True, "result": {"message_id": 42}})

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="T", chat_id=123, timeout=7.5)
    data = bot.send_message("hello", parse_mode="Markdown")
    assert data["ok"] is True
    assert captured["url"].endswith("/sendMessage")
    payload = captured["kwargs"].get("json")
    assert payload["chat_id"] == 123
    assert payload["text"] == "hello"
    assert payload["parse_mode"] == "Markdown"
    assert captured["kwargs"].get("timeout") == 7.5


def test_send_message_extra_kwargs(monkeypatch):
    captured = {}

    def fake_post(url, *args, **kwargs):
        captured["kwargs"] = kwargs
        return FakeResponse({"ok": True})

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="t", chat_id=1)
    bot.send_message("x", disable_notification=True, disable_web_page_preview=False)
    payload = captured["kwargs"]["json"]
    assert payload["disable_notification"] is True
    assert payload["disable_web_page_preview"] is False


def test_send_message_api_returns_error_raises_runtime(monkeypatch):
    def fake_post(url, *args, **kwargs):
        return FakeResponse({"ok": False, "description": "bad"})

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="t", chat_id=1)
    with pytest.raises(RuntimeError):
        bot.send_message("msg")


def test_send_message_httpx_request_error_propagates(monkeypatch):
    def fake_post(url, *args, **kwargs):
        raise httpx2.RequestError("network failure")

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="t", chat_id=1)
    with pytest.raises(httpx2.RequestError):
        bot.send_message("msg")


def test_send_returns_true_on_success(monkeypatch):
    def fake_post(url, *args, **kwargs):
        return FakeResponse({"ok": True, "result": {"message_id": 99}})

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="T", chat_id=999)
    assert bot.send("test") is True


def test_send_returns_false_on_error(monkeypatch):
    def fake_post(url, *args, **kwargs):
        raise httpx2.RequestError("network failure")

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="T", chat_id=999)
    assert bot.send("test") is False


def test_send_rich_message_with_html(monkeypatch):
    captured = {}

    def fake_post(url, *args, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse({"ok": True, "result": {"message_id": 1}})

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="T", chat_id=999)
    resp = bot.send_rich_message(html="<b>bold</b>")
    assert resp["ok"] is True
    assert captured["url"].endswith("/sendRichMessage")
    payload = captured["kwargs"]["json"]
    assert payload["chat_id"] == 999
    assert payload["rich_message"] == {"html": "<b>bold</b>"}


def test_send_rich_message_with_markdown(monkeypatch):
    captured = {}

    def fake_post(url, *args, **kwargs):
        captured["kwargs"] = kwargs
        return FakeResponse({"ok": True, "result": {"message_id": 1}})

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="T", chat_id=999)
    resp = bot.send_rich_message(markdown="**bold**")
    assert resp["ok"] is True
    payload = captured["kwargs"]["json"]
    assert payload["rich_message"] == {"markdown": "**bold**"}


def test_send_rich_message_neither_html_nor_markdown_raises():
    bot = TelegramBot(token="t", chat_id=1)
    with pytest.raises(ValueError):
        bot.send_rich_message()


def test_send_rich_message_both_html_and_markdown_raises():
    bot = TelegramBot(token="t", chat_id=1)
    with pytest.raises(ValueError):
        bot.send_rich_message(html="<b>x</b>", markdown="**x**")


def test_send_rich_message_extra_kwargs(monkeypatch):
    captured = {}

    def fake_post(url, *args, **kwargs):
        captured["kwargs"] = kwargs
        return FakeResponse({"ok": True, "result": {"message_id": 1}})

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="T", chat_id=42)
    resp = bot.send_rich_message(
        html="<b>bold</b>",
        disable_notification=True,
        protect_content=True,
    )
    assert resp["ok"] is True
    payload = captured["kwargs"]["json"]
    assert payload["chat_id"] == 42
    assert payload["rich_message"] == {"html": "<b>bold</b>"}
    assert payload["disable_notification"] is True
    assert payload["protect_content"] is True


def test_send_rich_message_api_error_raises(monkeypatch):
    def fake_post(url, *args, **kwargs):
        return FakeResponse({"ok": False, "description": "bad"})

    monkeypatch.setattr(httpx2, "post", fake_post)

    bot = TelegramBot(token="t", chat_id=1)
    with pytest.raises(RuntimeError):
        bot.send_rich_message(html="<b>x</b>")
