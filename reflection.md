# Reflection


**1. Which issues were the easiest and which were the hardest to fix?**
The easiest were the mechanical ones: Flake8's blank-line and line-length errors, the unused import, the missing docstrings and the `printAlerts` rename. Each had one obvious fix and the tool told me exactly where. The hardest were the ones where the fix changed behaviour. Replacing `mktemp` with `mkstemp` meant understanding *why* it is unsafe (race condition) and handling a file descriptor correctly. Removing `logs=[]` meant deciding what the "total registrations" message should actually mean. The bare `except` forced me to decide which failures were really expected.

**2. Did the tools report any false positives?**
Not really, but some findings needed judgement. Bandit's B101 (`assert`) is only Low severity and would be harmless in a throwaway script, but here the assert was used for runtime validation, so it was a real weakness. Pylint's `global-statement` (W0603) is a design preference rather than a bug, and I could have silenced it with a comment; I chose to remove the global instead. The key lesson was to read each message and decide, not to suppress findings blindly.

**3. How would you integrate static analysis into a real development workflow?**
Run Flake8 and Pylint as a pre-commit hook so style and quality problems never reach the repository, and run all three tools in CI (e.g. GitHub Actions) on every pull request, failing the build if Bandit reports Medium/High findings or the Pylint score drops below an agreed threshold (e.g. 9.5). Configure them in the repo (`.pylintrc`, `setup.cfg`/`tox.ini`, `bandit.yaml`) so every developer gets identical results, and allow justified suppressions (`# nosec`, `# pylint: disable=`) only with a comment explaining why.

**4. What tangible improvements did you see after the fixes?**
The Pylint score went from 6.55 to 10.00, Bandit went from 2 findings to 0 and Flake8 from 12 to 0. More importantly, the program became more correct: a negative interval no longer marks every asset overdue, duplicate and empty ids are rejected, bad dates can no longer crash the report, files are always closed, and the temp file is created securely. The code is also easier to read and test because every function has a docstring, there is no hidden global state, and importing the module no longer runs the program. The biggest takeaway is that static analysis is necessary but not sufficient: the worst bugs here (negative interval, overwriting assets) were found only by running the program and reading its output.
