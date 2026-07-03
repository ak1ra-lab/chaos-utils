"""Pydantic V2 models for :mod:`chaos_utils.notify` configuration.

Each model declares the required fields for its corresponding notifier
class.  The top-level :class:`ConfigFile` model validates a complete
TOML config file so that you get a descriptive error before a single
message is sent.

Usage from TOML:

.. code-block:: toml

    [notify.my_bot]
    type = "dingtalk"
    access_token = "..."

    [notify.another_bot]
    type = "telegram"
    token = "..."
    default_chat_id = "-100..."

Validating:

.. code-block:: python

    import tomllib
    from chaos_utils.notify.config import ConfigFile, NotifierConfig

    raw = tomllib.loads(path.read_text())
    cfg = ConfigFile.model_validate(raw)

    for name, entry in cfg.notify.items():
        bot = entry.build()
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from chaos_utils.notify.dingtalk import DingTalkBot
from chaos_utils.notify.feishu import FeishuBot
from chaos_utils.notify.telegram import TelegramBot
from chaos_utils.notify.wechat import WechatWorkBot


class _BaseConfig(BaseModel):
    """Shared base — not meant to be instantiated directly."""

    model_config = ConfigDict(extra="forbid")


class DingTalkConfig(_BaseConfig):
    """Configuration for :class:`DingTalkBot`.

    Webhook URL: ``https://oapi.dingtalk.com/robot/send?access_token=<TOKEN>``
    """

    type: Literal["dingtalk"] = Field(
        default="dingtalk",
        description="Notifier type discriminator.",
    )
    access_token: str = Field(
        ...,
        min_length=1,
        description="Access token from the DingTalk bot webhook URL.",
    )
    secret: str = Field(
        default="",
        description="Optional signing secret. When non-empty every request is signed with HMAC-SHA256.",
    )

    def build(self) -> DingTalkBot:
        return DingTalkBot(
            access_token=self.access_token,
            secret=self.secret,
        )


class FeishuConfig(_BaseConfig):
    """Configuration for :class:`FeishuBot`.

    Webhook URL: ``https://open.feishu.cn/open-apis/bot/v2/hook/<HOOK_ID>``
    """

    type: Literal["feishu"] = Field(
        default="feishu",
        description="Notifier type discriminator.",
    )
    webhook_url: str = Field(
        ...,
        min_length=1,
        description="Full webhook URL from the Feishu bot settings.",
    )
    secret: str = Field(
        default="",
        description="Optional signing secret for message verification.",
    )

    def build(self) -> FeishuBot:
        return FeishuBot(
            webhook_url=self.webhook_url,
            secret=self.secret,
        )


class TelegramConfig(_BaseConfig):
    """Configuration for :class:`TelegramBot`.

    API base URL: ``https://api.telegram.org/bot<TOKEN>``
    """

    type: Literal["telegram"] = Field(
        default="telegram",
        description="Notifier type discriminator.",
    )
    token: str = Field(
        ...,
        min_length=1,
        description="Bot token like '123456:ABC-DEF...'.",
    )
    chat_id: int | str = Field(
        ...,
        description="Target chat identifier (user, group, or channel).",
    )
    timeout: float = Field(
        default=5.0,
        ge=0.1,
        description="HTTP request timeout in seconds.",
    )

    def build(self) -> TelegramBot:
        return TelegramBot(
            token=self.token,
            chat_id=self.chat_id,
            timeout=self.timeout,
        )


class WechatWorkConfig(_BaseConfig):
    """Configuration for :class:`WechatWorkBot`.

    Webhook URL: ``https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=<KEY>``
    """

    type: Literal["wechat"] = Field(
        default="wechat",
        description="Notifier type discriminator.",
    )
    key: str = Field(
        ...,
        min_length=1,
        description="The webhook key from the WeChat Work bot webhook URL.",
    )

    def build(self) -> WechatWorkBot:
        return WechatWorkBot(key=self.key)


NotifierConfig = Annotated[
    Union[
        DingTalkConfig,
        FeishuConfig,
        TelegramConfig,
        WechatWorkConfig,
    ],
    Field(discriminator="type"),
]


class ConfigFile(BaseModel):
    """Root model for a ``notify.toml`` file.

    .. code-block:: toml

        [notify.alerts]
        type = "wechat"
        key = "..."

        [notify.logbot]
        type = "telegram"
        token = "..."
        default_chat_id = "-100..."
    """

    model_config = ConfigDict(extra="forbid")

    notify: dict[str, NotifierConfig] = Field(
        default_factory=dict,
        description="Mapping of notifier name → configuration.",
    )
