# AGENTS.md

## What This Project Does

`chaos-utils` is a Python library — a collection of utility helpers. It is NOT a CLI application; the only CLI entry point is `python3 -m chaos_utils.notify.cli`, which is a convenience tool for sending IM notifications.

## Environment & Tooling — CRITICAL

- ALWAYS use `uv` for dependency management and command execution. Recipes are wrapped in `justfile` for convenience; you can also use `uv` directly.
- Sync dependencies with `just sync`.
- Lint and format with `just lint`; run static typing with `just typecheck`.
- Run tests with `just test` or `uv run pytest -v tests/`.
- Build docs with `just docs-build` and preview them with `just docs-serve`.
- DO NOT use ad hoc `pip install` commands instead of updating `pyproject.toml`.
- DO NOT edit generated output under `site/`; rebuild it from source.

## Template & Versioning

- Versioning is dynamic: driven by Git tags via `hatch-vcs`. DO NOT manually bump a version string in `pyproject.toml`.
- Releases: push a Git tag starting with `v` (e.g. `v0.1.0`). CI will automatically build and publish to PyPI.
- Copier updates: run `uv run copier update --trust`. DO NOT manually edit `.copier-answers.yaml`.
- Pre-commit hooks are configured and will block invalid commits.

## Conventions

- Library code lives under `src/chaos_utils/` (flat submodules + `notify/` subpackage).
- The only CLI is `chaos_utils.notify.cli`, using stdlib `argparse` with `argcomplete` for shell completion. There is NO top-level CLI entry point — this is a library, not an application.
- Tests live under `tests/` and should track public behavior and CLI behavior.
- Documentation source lives under `docs/`. Docs configuration lives in `zensical.toml`.
- Project metadata and dependency groups are defined in `pyproject.toml`; treat that file as the source of truth.

## Module Layout

| Module | Purpose |
|--------|---------|
| `chaos_utils.dict_utils` | Dictionary helpers (`deep_merge`) |
| `chaos_utils.text_utils` | Text encoding detection, file I/O, JSON, Base64 |
| `chaos_utils.gitignore` | `.gitignore`-aware filesystem traversal |
| `chaos_utils.logging` | Structured logging (`JsonFormatter`, `setup_logger`) |
| `chaos_utils.tarfile` | Zstd-compressed tar archive support |
| `chaos_utils.notify` | IM notification channels (DingTalk, Feishu, Telegram, WeChat Work) |
| `chaos_utils.notify.cli` | Send test notifications via command line |
| `chaos_utils.notify.config` | Pydantic V2 models for notification config validation |

## Testing Guidelines

- Update tests when CLI behavior, public APIs, or package layout changes.
- Test the notify CLI via `main()` or by invoking `_build_parser()`.
- Keep docs commands working when changing docs pages, API docs wiring, or navigation structure.

## Common Operations

```shell
just sync          # sync development dependencies
just lint          # lint and format source plus tests
just typecheck     # run Astral ty over src/
just test          # run the pytest suite
just docs-build    # build the static docs site with Zensical
just docs-serve    # preview docs locally on the configured dev address
```
