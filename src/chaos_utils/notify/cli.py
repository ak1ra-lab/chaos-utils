"""CLI tool for sending notifications via configured IM channels.

Usage:
    python3 -m chaos_utils.notify.cli -n <name> -m "message text"
    python3 -m chaos_utils.notify.cli -n <name> -f /path/to/message.txt
    echo "alert" | python3 -m chaos_utils.notify.cli -n <name>
    python3 -m chaos_utils.notify.cli -c config/notify.toml -n <name> -M -m "**bold**"

Config file format (TOML)::

    [notify.my_telegram]
    type = "telegram"
    token = "..."
    chat_id = "..."

    [notify.my_dingtalk]
    type = "dingtalk"
    access_token = "..."
    secret = "..."

    [notify.my_feishu]
    type = "feishu"
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/..."
    secret = "..."

    [notify.my_wechat]
    type = "wechat"
    key = "..."

Config is validated with Pydantic V2 models defined in
:mod:`chaos_utils.notify.config`.  Invalid fields or unknown keys
produce a descriptive error before any message is sent.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from chaos_utils.logging import setup_logger
from chaos_utils.notify.config import ConfigFile
from chaos_utils.notify.dingtalk import DingTalkBot
from chaos_utils.notify.telegram import TelegramBot
from chaos_utils.notify.wechat import WechatWorkBot

logger = setup_logger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send notification via configured IM channel.",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config/notify.toml",
        help="Path to the TOML config file (default: config/notify.toml)",
    )
    parser.add_argument(
        "-n",
        "--name",
        required=True,
        help="Notifier name defined in the config file.",
    )
    msg_group = parser.add_mutually_exclusive_group()
    msg_group.add_argument(
        "-m",
        "--message",
        help="Message content to send.",
    )
    msg_group.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Read message content from a file.",
    )
    parser.add_argument(
        "-M",
        "--markdown",
        action="store_true",
        help="Send as markdown (where supported).",
    )
    return parser


def _resolve_message(args: argparse.Namespace) -> str:
    if args.file:
        return args.file.read_text(encoding="utf-8")
    if args.message:
        return args.message
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        if data:
            return data
    logger.error("no message provided; use -m, -f, or pipe via stdin")
    sys.exit(1)


def _load_config(config_path: str, name: str) -> Any:
    path = Path(config_path)
    if not path.exists():
        logger.error("config file not found: %s", path)
        sys.exit(1)

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        cfg = ConfigFile.model_validate(raw)
    except ValidationError as exc:
        logger.error("invalid config (%s):\n%s", path, exc)
        sys.exit(1)

    if name not in cfg.notify:
        available = ", ".join(sorted(cfg.notify)) or "(none)"
        logger.error(
            "notifier '%s' not found in config. available: %s", name, available
        )
        sys.exit(1)

    entry = cfg.notify[name]
    return entry.build()


def _send_markdown(bot: Any, text: str) -> Any:
    if isinstance(bot, DingTalkBot):
        title = text.split("\n")[0]
        return bot.send_markdown(title, text)
    if isinstance(bot, TelegramBot):
        return bot.send_rich_message(markdown=text)
    if isinstance(bot, WechatWorkBot):
        return bot.send_markdown_v2(text)
    # FeishuBot only supports plain text via send()
    return bot.send(text)


def _send_text(bot: Any, text: str) -> Any:
    if isinstance(bot, DingTalkBot):
        return bot.send_text(text)
    if isinstance(bot, TelegramBot):
        return bot.send_message(text)
    if isinstance(bot, WechatWorkBot):
        return bot.send_text(text)
    # FeishuBot only has send() → bool
    return bot.send(text)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    message = _resolve_message(args)
    if not message.strip():
        logger.error("message is empty")
        sys.exit(1)

    bot = _load_config(args.config, args.name)

    try:
        if args.markdown:
            result = _send_markdown(bot, message)
        else:
            result = _send_text(bot, message)
    except Exception:
        logger.exception("failed to send notification")
        sys.exit(1)

    if isinstance(result, bool):
        print("ok" if result else "failed")
        sys.exit(0 if result else 1)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
