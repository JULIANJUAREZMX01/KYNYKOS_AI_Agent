# Sentinel's Security Journal

## 2026-11-06 - Command Argument Injection in System Tools
**Vulnerability:** In `ToolExecutor._network_scan`, user input (`target`) was passed directly into `subprocess.run(["ping", "-n", "1", target], shell=False)`. While `shell=False` prevents shell command chaining (`;`, `&&`), it does not prevent command option/argument injection (e.g. passing flags like `-t`, `-c 5`, or malicious options).
**Learning:** `shell=False` is insufficient if the subprocess arguments themselves are untrusted. Tools executing OS utilities (`ping`, `taskkill`, `git`, etc.) must validate and sanitize all argument values before subprocess dispatch.
**Prevention:** Validate network targets against `ipaddress.ip_address` or a strict hostname regex pattern, and explicitly forbid flags starting with `-` or strings containing whitespace/control characters.

## 2026-11-07 - Process Termination Option Injection in manage_processes
**Vulnerability:** In `ToolExecutor._manage_processes`, user-supplied `name` argument was directly interpolated into `taskkill` subprocess arguments (`taskkill /F /IM {filter_name}*` or `/PID {filter_name}`). Unsanitized inputs containing switches like `/s`, `/u`, `/p`, or spaces could manipulate taskkill execution.
**Learning:** Command-line utilities on Windows (such as `taskkill`, `shutdown`) treat `/` as option prefixes. Relying solely on `shell=False` does not prevent switches starting with `/` or `-` from being interpreted by the utility.
**Prevention:** Strictly validate process identifiers: enforce `filter_name.isdigit()` for PIDs and validate process image names with regex `^[a-zA-Z0-9_.-]+$`, while explicitly rejecting leading `-` or `/` and whitespace.

## 2026-11-08 - Git Option Injection and Path Traversal in git_operation
**Vulnerability:** In `ToolExecutor._git_operation`, `repo_path` was passed to `subprocess.run(cwd=repo_path)` without directory boundary checks, enabling path traversal. Additionally, `operation` validation relied on substring checking (`if not any(op in operation.lower() for op in safe_ops)`), allowing arbitrary git subcommands (e.g. `push`, `config`, `clone`) and dangerous flags (such as `--upload-pack`, `-c`, `--exec-path`, `--output`) that permit command execution or arbitrary file writes.
**Learning:** Checking substring presence in command strings allows attackers to bypass security filters by appending malicious arguments after a permitted keyword. Furthermore, CLI subcommands must be parsed and validated as tokens, and flags with side effects must be explicitly denied or whitelisted.
**Prevention:** Validate working directories using strict safe path checks (`_is_safe_path`). Parse command strings into argument lists with `shlex.split`, verify that `cmd_args[0]` strictly equals an approved subcommand, and explicitly reject dangerous flags (`--upload-pack`, `--exec-path`, `-c`, etc.).
