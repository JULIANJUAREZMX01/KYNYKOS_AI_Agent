# Sentinel Journal 🛡️

## 2026-11-04 - Git Subcommand Whitelisting and Flag Injection Defense
**Vulnerability:** `ToolExecutor._git_operation` checked if allowed operation names (`status`, `log`, etc.) existed as substrings in the raw input command string instead of validating the actual sub-command token. Additionally, dangerous flags like `--upload-pack`, `--receive-pack`, or `-c` can trigger arbitrary command execution or config overrides in git even when shell=False. In `ToolExecutor._self_repair`, `git pull` and `pip install` were invoked via `shell=True`.
**Learning:** Checking substrings on user-supplied CLI arguments leaves a significant command injection and bypass window. When wrapping CLIs like `git`, validate the exact positional subcommand against an allowlist, inspect arguments for dangerous flags (such as option-based execution vectors), and never execute with `shell=True`.
**Prevention:** Always parse CLI strings using `shlex.split`, validate `argv[0]` strictly against a subcommand whitelist, scan remaining flags against blocked execution options, and pass command lists to `subprocess.run(shell=False)`.
