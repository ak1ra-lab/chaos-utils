# chaos-utils

Collection of handy utils written in Python 3

## Installation

```shell
pip install chaos-utils
```

## Development

```shell
uv sync --group dev
```

### Common tasks

```shell
just lint          # lint and format
just typecheck     # run static type checker
just test          # run the test suite
just docs-build    # build the static docs site
just docs-serve    # preview docs locally
```

## Module overview

| Module | Purpose |
|--------|---------|
| `chaos_utils.dict_utils` | Dictionary helpers (`deep_merge`) |
| `chaos_utils.text_utils` | Text encoding detection, file I/O, JSON, Base64 |
| `chaos_utils.gitignore` | `.gitignore`-aware filesystem traversal |
| `chaos_utils.logging` | Structured logging (`JsonFormatter`, `setup_logger`) |
| `chaos_utils.tarfile` | Zstd-compressed tar archive support |
| `chaos_utils.notify` | IM notifications (DingTalk, Feishu, Telegram, WeChat Work) |

## Notify CLI

Send a test notification via the configured IM channel:

```shell
python3 -m chaos_utils.notify.cli -n <name> -m "hello"
```

Shell completion is available via argcomplete:

```shell
eval "$(register-python-argcomplete python3)"
```

Full CLI reference and config format are documented in the module docstring of `chaos_utils.notify.cli`.
