# chaos-utils

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ak1ra-lab/chaos-utils/.github%2Fworkflows%2Fpublish-to-pypi.yaml)](https://github.com/ak1ra-lab/chaos-utils/actions/workflows/publish-to-pypi.yaml)
[![PyPI - Version](https://img.shields.io/pypi/v/chaos-utils)](https://pypi.org/project/chaos-utils/)
[![PyPI - Version](https://img.shields.io/pypi/v/chaos-utils?label=test-pypi&pypiBaseUrl=https%3A%2F%2Ftest.pypi.org)](https://test.pypi.org/project/chaos-utils/)
[![Docs](https://img.shields.io/badge/docs-online-0a7ea4)](https://ak1ra-lab.github.io/chaos-utils/)

Collection of handy utils written in Python 3

## Installation

```shell
pip install chaos-utils
```

## Modules

- **`dict_utils`** — recursive dictionary merging
- **`text_utils`** — text encoding detection, file I/O, JSON, Base64
- **`gitignore`** — `.gitignore`-aware filesystem traversal
- **`logging`** — structured logging with `JsonFormatter`
- **`tarfile`** — Zstd-compressed tar archive support
- **`notify`** — IM notifications via DingTalk, Feishu, Telegram, WeChat Work

See the [documentation](https://ak1ra-lab.github.io/chaos-utils/) for full API reference.

## Development

```shell
just lint
just typecheck
just test
just docs-build
```

## Documentation

The published documentation site lives at <https://ak1ra-lab.github.io/chaos-utils/>.
