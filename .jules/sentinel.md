# Sentinel's Security Journal

## 2026-11-06 - Command Argument Injection in System Tools
**Vulnerability:** In `ToolExecutor._network_scan`, user input (`target`) was passed directly into `subprocess.run(["ping", "-n", "1", target], shell=False)`. While `shell=False` prevents shell command chaining (`;`, `&&`), it does not prevent command option/argument injection (e.g. passing flags like `-t`, `-c 5`, or malicious options).
**Learning:** `shell=False` is insufficient if the subprocess arguments themselves are untrusted. Tools executing OS utilities (`ping`, `taskkill`, `git`, etc.) must validate and sanitize all argument values before subprocess dispatch.
**Prevention:** Validate network targets against `ipaddress.ip_address` or a strict hostname regex pattern, and explicitly forbid flags starting with `-` or strings containing whitespace/control characters.
