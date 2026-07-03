# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-07-03

### Added

- Introduce `chaos_utils.notify` subpackage consolidating IM notification modules (Telegram, DingTalk, Feishu, WeChat Work)
- Telegram Rich Markdown/Rich HTML support via `sendRichMessage` API with `send_rich_message(html=|markdown=)`
- CLI entry point `python3 -m chaos_utils.notify.cli` for sending test notifications
- Pydantic V2 config models (`ConfigFile`, `NotifierConfig`) with discriminated union on channel type
- `__version__` from package metadata in `chaos_utils.__init__`

### Changed

- `TelegramBot`: require `chat_id` as required constructor parameter; remove `default_chat_id`

### Removed

- Remove `read_toml` thin wrapper; use stdlib `tomllib` directly
- Remove unused WeChat Work bot methods (`send_image`, `send_news`, `send_file`, `upload_media`) and exception classes
- Remove `_post_json` / `_get_json` helper methods from `BaseNotifier`

### Fixed

- Add missing type annotations in `logging.py`, `tarfile.py`, `text_utils.py`

## [0.4.2] - 2026-06-10

### Changed

- Replace `httpx` with `httpx2` library

### Fixed

- Use `object.__setattr__` in logger setup to avoid recursion

## [0.4.1] - 2026-03-01

### Added

- Add `TextFormatter` to append `extra=` fields in structured log output

## [0.4.0] - 2026-02-28

### Added

- Add `README.md` with module overview and API reference

### Changed

- Refactor `logging.py`: replace hardcoded `logging_dir` with XDG-aware `_resolve_logging_dir`
- Rewrite `CHANGELOG.md` to follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format; remove `cliff.toml`

### Fixed

- Surface `extra=` fields in `JsonFormatter` output

## [0.3.1] - 2025-12-30

### Fixed

- Improve encoding detection in `detect_encoding` function

## [0.3.0] - 2025-12-19

### Added

- Add `telegram.py` with Telegram bot notification support and corresponding tests

### Fixed

- Enhance encoding detection with UTF-8 validation

## [0.2.0] - 2025-11-05

### Added

- Add `dingtalk.py` with DingTalk webhook notification support and corresponding tests
- Add `wechat.py` with WeChat Work webhook notification support and corresponding tests
- Implement comprehensive docstrings throughout the codebase

### Removed

- Remove `http_utils.py`
- Remove nox configuration, add `ruff.sh` for linting

## [0.1.2] - 2025-11-01

### Added

- Add `http_utils.py`

### Fixed

- Fix uv build step in CI workflow

## [0.1.1] - 2025-11-01

### Changed

- Update `pyproject.toml` configuration

## [0.1.0] - 2025-11-01

### Added

- Migrate `src` and `tests` from chaos-box
- Implement GitHub Actions CI workflows

[Unreleased]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ak1ra-lab/chaos-utils/releases/tag/v0.1.0
