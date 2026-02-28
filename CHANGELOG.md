# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ak1ra-lab/chaos-utils/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ak1ra-lab/chaos-utils/releases/tag/v0.1.0
