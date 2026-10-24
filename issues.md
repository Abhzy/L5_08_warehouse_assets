# Issues found and fixed — `maintenance_system.py`

Tools: Pylint, Bandit, Flake8 (reports in `reports/before/` and `reports/after/`).
Scores: **Pylint 6.55/10 → 10.00/10**, **Bandit 2 issues → 0**, **Flake8 12 issues → 0**.
Line numbers refer to the **original** file.

## Issues that matter most (ordered by severity)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Insecure temp file: `tempfile.mktemp()` (Bandit B306, **Medium**) | Security | 40 | `mktemp` only returns a *name*. Between generating it and `open()`, another process can create a file or symlink at that path (race condition / symlink attack). | Use `tempfile.mkstemp()`, which atomically creates the file with owner-only permissions, and write through `os.fdopen(fd, ...)` inside a `with` block. |
| Mutable default argument `logs=[]` (Pylint W0102) | Bug | 10 | The list is created once and shared by every call, so state leaks between calls ("total registrations" counter grows across calls and across tests/imports). | Removed the hidden shared list; the function now reports `len(assets)` from the explicit registry. |
| Bare `except:` (Pylint W0702, Flake8 E722) | Bug / Quality | 17-18 | Swallows *every* exception (including `KeyboardInterrupt`), and hides the real cause. It only ever meant "unknown asset". | Check `asset_id in assets` explicitly and catch only `ValueError` from `strptime`; log the specific reason with `logging.warning`. |
| `assert` used for runtime validation (Bandit B101, Low) | Security / Bug | 61 | `assert` is stripped when Python runs with `-O`, so the check silently disappears. | Replaced with an explicit `if not assets:` check that logs an error and exits cleanly. |
| Resource handling: `open()` without `with`/encoding (Pylint R1732, W1514) | Quality | 34, 41 | File is not closed if `write()` raises, and encoding depends on the OS locale. | `with open(..., encoding="utf-8")` plus `json.dump` directly into the file. |
| `global` statement (Pylint W0603) | Design | 30 | Rebinding a module global makes state hard to reason about and test. | Interval kept in a `settings` dict that is mutated in place; no `global` needed. |
| Unused import `logging` (Pylint W0611, Flake8 F401) | Style | 2 | Dead import. | Now actually used for warnings/errors (replaces ad-hoc `print`s for failures). |
| Missing docstrings (Pylint C0114, C0116 ×9) | Style | 1, 10-50 | No module/function documentation. | Added a module docstring and one for every function. |
| Non-snake_case name `printAlerts` (Pylint C0103) | Style | 46 | Violates PEP 8 naming. | Renamed to `print_alerts`. |
| Iterating dict by key then indexing (Pylint C0206) | Style | 23-25 | `for a in assets: assets[a]` does a redundant lookup. | Iterate `assets.items()`. |
| Blank lines / line length (Flake8 E302 ×9, E305, E501) | Style | 10-66 | Functions separated by one blank line; line 11 is 98 characters. | Two blank lines between top-level definitions; long lines wrapped. |

## Logic bugs found by running the program (no tool reports these)

Running the original printed `Registered  - total...` for an empty id, turned `FL-01` from a Forklift into a Crane, and flagged *every* asset as overdue, even ones registered a second ago.

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Negative service interval accepted | Bug (High impact) | 29-31, 56 | `change_interval(-30)` makes `now - last > timedelta(days=-30)` true for every asset, so all assets, including brand-new ones, raise "overdue" alerts. | `change_interval` validates a positive integer and rejects anything else (returns `False`, logs a warning). |
| Duplicate registration silently overwrites | Bug | 10-13, 54 | Registering `FL-01` twice replaced "Forklift" with "Crane" **and reset `last_service` to today**, wiping the service history. | `register_asset` refuses an id that already exists. |
| Empty asset id accepted | Bug | 10-13, 53 | `""` was stored as a real asset (and later shown in alerts as a blank name). | Reject empty / whitespace-only ids. |
| Service date never validated | Bug | 15-19, 59-60 | Any string (`"hello"`, `"31-02-2025"`) was stored; the program then **crashed** later in `strptime` inside `due_for_inspection`. | `update_service_date` parses the date with `strptime` *before* storing it and rejects bad input. |
| Update to unknown asset hid its cause | Bug | 55 | `XX-99` failure printed a vague message via the bare `except`. | Explicit "unknown asset" check with a clear message. |
| `main()` runs on import | Design | 66 | Importing the module (e.g. for tests or Pylint's analysis) executes the whole demo and prompts for input. | Wrapped in `if __name__ == "__main__":`; `EOFError` from `input()` handled. |

## Commits
1. `Fix Bandit findings` — B306 `mktemp` → `mkstemp`, B101 `assert` → explicit check.
2. `Fix Pylint findings` — everything in the Pylint table + the logic/validation bugs above.
3. `Fix Flake8 findings` — E302/E305/E501 formatting.
