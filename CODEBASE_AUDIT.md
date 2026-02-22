# Codebase Audit Report

## Scope
A static review of the Scrapling repository plus automated checks (`pytest -q`, `ruff check`) to identify potential runtime bugs, logic issues, and best-practice gaps.

## Critical

### 1) Incorrect file-descriptor handling in shell HTML preview
- **Location:** `scrapling/core/shell.py`
- **Issue:** `show_page_in_browser` uses `open(fd, "w", ...)` where `fd` is an integer file descriptor returned by `tempfile.mkstemp`.
- **Impact:** Raises `TypeError` at runtime when users call `view(page)`, breaking a documented shell helper.
- **Suggested fix:** Replace with `os.fdopen(fd, "w", encoding=...)`, or close `fd` and reopen using `fname`.

## High

### 2) Bare `raise` in checkpoint restore path
- **Location:** `scrapling/spiders/engine.py`
- **Issue:** `_restore_from_checkpoint` executes a bare `raise` when checkpointing is disabled.
- **Impact:** If this method is called outside an active exception context, Python raises `RuntimeError: No active exception to reraise`.
- **Suggested fix:** Return `False` (or raise a specific exception type with message) instead of bare `raise`.

### 3) Request object mutation during fetch may cause hidden side effects
- **Location:** `scrapling/spiders/session.py`
- **Issue:** `request._session_kwargs.pop("method", "GET")` mutates request state while fetching.
- **Impact:** Retried/reused request objects can lose original method metadata, creating hard-to-trace behavior differences.
- **Suggested fix:** Read method with `.get(...)` from a local copy of kwargs, then pass copied kwargs onward.

### 4) Nondeterministic request fingerprint when `include_kwargs=True`
- **Location:** `scrapling/spiders/request.py`
- **Issue:** Fingerprint input builds kwargs from `"".join(set(...))`; set iteration order is not deterministic.
- **Impact:** Same logical request may produce different fingerprints across runs/processes, weakening deduplication consistency.
- **Suggested fix:** Use sorted keys/values (e.g., sorted tuple/list) before concatenation or hash structured JSON with deterministic ordering.

## Medium

### 5) Mutable class defaults on spider base class
- **Location:** `scrapling/spiders/spider.py`
- **Issue:** `start_urls` and `allowed_domains` are mutable class attributes.
- **Impact:** Subclass or instance-level accidental mutations can leak across instances/tests.
- **Suggested fix:** Initialize mutable containers per instance in `__init__` or treat class-level values as immutable tuples/frozensets.

### 6) Scheduler restore does not reset in-memory queue state before loading snapshot
- **Location:** `scrapling/spiders/scheduler.py`
- **Issue:** `restore` repopulates queue/`_pending`/`_seen` without explicitly clearing existing entries.
- **Impact:** If restore is called on non-fresh scheduler, duplicate work and stale state can persist.
- **Suggested fix:** Clear `_queue`, `_pending`, and `_seen` prior to restoration (or assert scheduler is empty).

### 7) Destructor assumes fully initialized SQLite state
- **Location:** `scrapling/core/storage.py`
- **Issue:** `__del__` always calls `self.close()` without guarding partially initialized or already-closed resources.
- **Impact:** Destructor-time exceptions can occur during interpreter shutdown or failed initialization.
- **Suggested fix:** Add defensive checks/`contextlib.suppress` in `close`/`__del__`, and set connection/cursor to `None` after closing.

## Low

### 8) Import-time hard dependency behavior weakens partial usability
- **Locations:** multiple modules under `scrapling/engines`, `scrapling/spiders`, `scrapling/core/ai.py`
- **Issue:** Optional integrations are imported at module import-time; missing extras fail import/collection immediately.
- **Impact:** Users cannot run unaffected features without installing all extras; test collection breaks in minimal environments.
- **Suggested fix:** Defer optional imports into feature-specific code paths and raise actionable runtime errors.

### 9) Hygiene/lint debt in tests
- **Location:** multiple test files
- **Issue:** Ruff reports trailing whitespace, invalid `noqa`, bare `except`, and unused variables.
- **Impact:** Increases maintenance noise and can hide real issues.
- **Suggested fix:** Run `ruff check --fix` and manually clean non-fixable entries.

## Check Results Used During Audit
- `pytest -q`: failed during collection due to missing runtime dependencies and import-time optional dependency loading.
- `ruff check scrapling scrapling_web tests --output-format=concise`: reported style and correctness issues (including some non-auto-fixable items).
