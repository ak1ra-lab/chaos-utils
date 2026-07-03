# chaos-utils

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ak1ra-lab/chaos-utils/.github%2Fworkflows%2Fpublish-to-pypi.yaml)](https://github.com/ak1ra-lab/chaos-utils/actions/workflows/publish-to-pypi.yaml)
[![PyPI - Version](https://img.shields.io/pypi/v/chaos-utils)](https://pypi.org/project/chaos-utils/)
[![PyPI - Version](https://img.shields.io/pypi/v/chaos-utils?label=test-pypi&pypiBaseUrl=https%3A%2F%2Ftest.pypi.org)](https://test.pypi.org/project/chaos-utils/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ak1ra-lab/chaos-utils)

A small collection of utility helpers written in Python 3, used across
[ak1ra-lab](https://github.com/ak1ra-lab) projects.

## Installation

```bash
pip install chaos-utils
```

## Modules

### `dict_utils` — Dictionary helpers

| Symbol                                       | Description                                                                                                                                                    |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `deep_merge(d1, d2, *, deepcopy_first=True)` | Recursively merge two dicts. Keys in `d2` take precedence; nested mappings are merged rather than replaced. Uses an iterative stack to avoid recursion limits. |

### `text_utils` — Text and file helpers

| Symbol                                      | Description                                                                                                                                 |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `detect_encoding(filepath, num_bytes=8192)` | Detect the character encoding of a file. Tries UTF-8 first, then falls back to `chardet` with adaptive sampling for low-confidence results. |
| `iter_filepath_lines(filepath)`             | Iterate over the lines of a text file with automatic encoding detection.                                                                    |
| `read_json(filepath)`                       | Read and parse a JSON file, returning a `dict` or `list`.                                                                                   |
| `save_json(filepath, data, sort_keys=True)` | Serialize `data` to a JSON file with optional key sorting.                                                                                  |
| `b64decode(data)`                           | Decode a Base64-encoded string and return the decoded text.                                                                                 |

### `gitignore` — `.gitignore`-aware filesystem helpers

| Symbol                                         | Description                                                                                                    |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `load_directory_gitignore_specs(directory)`    | Recursively load all `.gitignore` files under `directory` and return a mapping of directory → `GitIgnoreSpec`. |
| `should_path_ignore(path, specs)`              | Return `True` if `path` matches any applicable `.gitignore` rule or lives inside a `.git` directory.           |
| `path_walk(directory)`                         | `os.walk`-style generator that yields `(dirpath, dirs, files)` as `Path` objects.                              |
| `path_walk_respect_gitignore(directory)`       | Like `path_walk` but skips entries that match `.gitignore` rules.                                              |
| `iter_files_with_respect_gitignore(directory)` | Yield every non-ignored file `Path` under `directory`.                                                         |
| `iter_dirs_with_respect_gitignore(directory)`  | Yield every non-ignored directory `Path` under `directory`.                                                    |

### `logging` — Logging helpers

| Symbol                         | Description                                                                                                                                                     |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `JsonFormatter`                | `logging.Formatter` subclass that serialises each record — including any `extra=` fields — as a single-line JSON string.                                        |
| `setup_logger(name, ...)`      | Create a logger with a `RotatingFileHandler` and an optional `StreamHandler`. Log files are placed under the XDG state directory (`$XDG_STATE_HOME/<app>/log`). |
| `setup_json_logger(name, ...)` | Like `setup_logger` but attaches `JsonFormatter` to produce structured JSON logs.                                                                               |

### `tarfile` — Zstd-compressed tar archives

| Symbol                     | Description                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `TarFileZstd`              | `tarfile.TarFile` subclass with `"zst"` open method for reading and writing `.tar.zst` archives via `pyzstd`. |
| `ZstdTarReader(name, ...)` | Convenience context manager that opens a `.tar.zst` archive for reading and ensures it is properly closed.    |

### `dingtalk` — DingTalk robot notifications

| Symbol                                        | Description                                                            |
| --------------------------------------------- | ---------------------------------------------------------------------- |
| `DingTalkBot(access_token, secret)`           | DingTalk group robot client with HMAC-SHA256 signature authentication. |
| `DingTalkBot.send_text(content, ...)`         | Send a plain-text message, optionally @-mentioning members.            |
| `DingTalkBot.send_markdown(title, text, ...)` | Send a Markdown-formatted message.                                     |

### `wechat` — WeChat Work notifications

| Symbol                                       | Description                                                                                                                                                         |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `WechatWorkApp(corpid, corpsecret, agentid)` | WeChat Work application client (corp API). Supports `send_text`, `send_markdown`, `send_image`, `send_news`, `send_news_multiple`, `send_file`, and `upload_media`. |
| `WechatWorkBot(key)`                         | WeChat Work webhook bot client. Supports `send_text`, `send_markdown`, `send_image`, `send_news`, `send_news_multiple`, and `send_file`.                            |

### `telegram` — Telegram bot notifications

| Symbol                                         | Description                                                                           |
| ---------------------------------------------- | ------------------------------------------------------------------------------------- |
| `TelegramBot(token, default_chat_id, timeout)` | Telegram Bot API client.                                                              |
| `TelegramBot.send_message(text, ...)`          | Send a text message with optional `parse_mode`, inline keyboard, and silent delivery. |
| `TelegramBot.send(text, **kwargs)`             | Convenience alias for `send_message`.                                                 |

## License

[MIT](LICENSE)
