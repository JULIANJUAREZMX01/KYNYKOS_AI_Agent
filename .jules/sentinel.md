# Sentinel's Security Journal

## 2026-11-06 - Command Argument Injection in System Tools
**Vulnerability:** In `ToolExecutor._network_scan`, user input (`target`) was passed directly into `subprocess.run(["ping", "-n", "1", target], shell=False)`. While `shell=False` prevents shell command chaining (`;`, `&&`), it does not prevent command option/argument injection (e.g. passing flags like `-t`, `-c 5`, or malicious options).
**Learning:** `shell=False` is insufficient if the subprocess arguments themselves are untrusted. Tools executing OS utilities (`ping`, `taskkill`, `git`, etc.) must validate and sanitize all argument values before subprocess dispatch.
**Prevention:** Validate network targets against `ipaddress.ip_address` or a strict hostname regex pattern, and explicitly forbid flags starting with `-` or strings containing whitespace/control characters.

## 2026-11-07 - Process Termination Option Injection in manage_processes
**Vulnerability:** In `ToolExecutor._manage_processes`, user-supplied `name` argument was directly interpolated into `taskkill` subprocess arguments (`taskkill /F /IM {filter_name}*` or `/PID {filter_name}`). Unsanitized inputs containing switches like `/s`, `/u`, `/p`, or spaces could manipulate taskkill execution.
**Learning:** Command-line utilities on Windows (such as `taskkill`, `shutdown`) treat `/` as option prefixes. Relying solely on `shell=False` does not prevent switches starting with `/` or `-` from being interpreted by the utility.
**Prevention:** Strictly validate process identifiers: enforce `filter_name.isdigit()` for PIDs and validate process image names with regex `^[a-zA-Z0-9_.-]+$`, while explicitly rejecting leading `-` or `/` and whitespace.

## 2026-11-08 - Git Option Injection and Unchecked Repository Path in git_operation
**Vulnerability:** In `ToolExecutor._git_operation`, user input `operation` was validated only via substring matching (`any(op in operation.lower() for op in safe_ops)`), allowing global option injection (e.g. `git -c core.fsmonitor=...` or `--upload-pack=...`), and `repo_path` was not validated against `_is_safe_path()`.
**Learning:** Substring checking on CLI strings allows attackers to prepend global flags or append dangerous switches while still matching an allowed keyword. Additionally, working directory arguments (`cwd`) in subprocess calls must be validated against directory traversal constraints.
**Prevention:** Parse command tokens with `shlex.split`, verify that `tokens[0]` matches an exact whitelist of allowed subcommands, block dangerous configuration options (`-c`, `--config-env`, `--upload-pack`, etc.), and validate `repo_path` with `_is_safe_path()`.
