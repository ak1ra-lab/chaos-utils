import httpx
import pytest

from chaos_utils.telegram import TelegramBot


class FakeResponse:
    """A minimal fake response to emulate httpx.Response for our tests."""

    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self):
        # emulate requests: raise only for >=400
        if self.status_code >= 400:
            # Use httpx.HTTPStatusError signature: message, request, response
            # For tests we can raise a generic httpx.HTTPStatusError with placeholders.
            raise httpx.HTTPStatusError("status error", request=None, response=None)

    def json(self):
        return self._json


def test_init_without_token_raises():
    with pytest.raises(ValueError):
        TelegramBot(token="")  # token required


def test_send_without_chat_id_and_no_default_raises():
    bot = TelegramBot(token="tkn", default_chat_id=None)
    # No network call needed because _resolve_chat_id will raise before httpx.post
    with pytest.raises(ValueError):
        bot.send_message("hi")


def test_send_message_success_and_payload(monkeypatch):
    captured = {}

    def fake_post(url, *args, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        # return ok payload
        return FakeResponse({"ok": True, "result": {"message_id": 42}})

    monkeypatch.setattr(httpx, "post", fake_post)

    bot = TelegramBot(token="T", default_chat_id=123, timeout=7.5)
    data = bot.send_message(
        "hello",
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup={"inline_keyboard": []},
    )
    assert data["ok"] is True
    # verify url and payload keys
    assert captured["url"].endswith("/sendMessage")
    payload = captured["kwargs"].get("json")
    assert payload["chat_id"] == 123
    assert payload["text"] == "hello"
    assert payload["parse_mode"] == "Markdown"
    assert payload["disable_web_page_preview"] is True
    # timeout used is instance timeout by default
    assert captured["kwargs"].get("timeout") == 7.5


def test_send_message_with_timeout_override(monkeypatch):
    captured = {}

    def fake_post(url, *args, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return FakeResponse({"ok": True})

    monkeypatch.setattr(httpx, "post", fake_post)

    bot = TelegramBot(token="t", default_chat_id=1, timeout=3.0)
    # override timeout to 1.2
    bot.send_message("x", timeout=1.2)
    assert captured["timeout"] == 1.2


def test_send_message_api_returns_error_raises_runtime(monkeypatch):
    def fake_post(url, *args, **kwargs):
        # API-level error (ok: False) should raise RuntimeError in client
        return FakeResponse({"ok": False, "description": "bad"})

    monkeypatch.setattr(httpx, "post", fake_post)

    bot = TelegramBot(token="t", default_chat_id=1)
    with pytest.raises(RuntimeError):
        bot.send_message("msg")


def test_send_message_httpx_request_error_propagates(monkeypatch):
    def fake_post(url, *args, **kwargs):
        raise httpx.RequestError("network failure")

    monkeypatch.setattr(httpx, "post", fake_post)

    bot = TelegramBot(token="t", default_chat_id=1)
    with pytest.raises(httpx.RequestError):
        bot.send_message("msg")


def test_send_alias_uses_send_message(monkeypatch):
    called = {}

    def fake_post(url, *args, **kwargs):
        called["ok"] = True
        return FakeResponse({"ok": True, "result": {"message_id": 99}})

    monkeypatch.setattr(httpx, "post", fake_post)

    bot = TelegramBot(token="T", default_chat_id=999)
    res = bot.send("alias test", disable_notification=True)
    assert res["ok"] is True
    assert called.get("ok") is True
