"""Tests for tool executor"""

import pytest
from pathlib import Path
from app.core.tools import ToolExecutor
from app.core.context import AgentContext


@pytest.fixture
def tool_executor(tmp_path):
    """Create tool executor with temporary workspace"""
    executor = ToolExecutor(str(tmp_path))
    return executor


@pytest.fixture
def agent_context():
    """Create test agent context"""
    ctx = AgentContext(
        session_id="test_session",
        user_id="test_user",
        channel="test"
    )
    return ctx


@pytest.mark.asyncio
async def test_tool_executor_initialization(tool_executor):
    """Test tool executor initialization"""
    assert tool_executor is not None
    assert "execute_shell" in tool_executor.tools
    assert "read_file" in tool_executor.tools
    assert "write_file" in tool_executor.tools


@pytest.mark.asyncio
async def test_read_file_not_found(tool_executor, agent_context):
    """Test reading non-existent file"""
    result = await tool_executor.read_file(
        {"path": "nonexistent.txt"},
        agent_context
    )
    assert "not found" in result.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_target",
    [
        "-t",
        "--help",
        "-c 5 127.0.0.1",
        "127.0.0.1; rm -rf /",
        "127.0.0.1 & id",
        "127.0.0.1 | whoami",
        "127.0.0.1`id`",
        "$(whoami)",
        "google.com -c 1",
        "bad target with spaces",
    ],
)
async def test_network_scan_rejects_argument_injection(tool_executor, agent_context, mocker, invalid_target):
    """Ensure network_scan blocks command option injection and malformed targets."""
    mock_run = mocker.patch("subprocess.run")
    result = await tool_executor.execute(
        "network_scan",
        {"target": invalid_target},
        agent_context
    )
    assert "Objetivo inválido" in result
    mock_run.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "valid_target",
    [
        "127.0.0.1",
        "::1",
        "localhost",
        "google.com",
        "sub.domain-example.com",
    ],
)
async def test_network_scan_allows_valid_targets(tool_executor, agent_context, mocker, valid_target):
    """Ensure network_scan accepts valid IPs and hostnames."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "OK"
    result = await tool_executor.execute(
        "network_scan",
        {"target": valid_target},
        agent_context
    )
    assert "ONLINE" in result
    mock_run.assert_called_once_with(["ping", "-n", "1", valid_target], shell=False, capture_output=True, text=True)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_filter",
    [
        "/s evil_server",
        "-t",
        "/F",
        "/PID 1234",
        "notepad.exe /t",
        "calc.exe && whoami",
        "chrome; echo pwned",
        "process with spaces",
        "-f",
    ],
)
async def test_manage_processes_rejects_argument_injection(tool_executor, agent_context, mocker, invalid_filter):
    """Ensure manage_processes blocks command switches and invalid characters for kill action."""
    mock_run = mocker.patch("subprocess.run")
    result = await tool_executor.execute(
        "manage_processes",
        {"action": "kill", "name": invalid_filter},
        agent_context
    )
    assert "inválido" in result
    mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_manage_processes_allows_valid_pid(tool_executor, agent_context, mocker):
    """Ensure manage_processes allows numeric PID."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""
    result = await tool_executor.execute(
        "manage_processes",
        {"action": "kill", "name": "1234"},
        agent_context
    )
    assert "terminado por orden superior" in result
    mock_run.assert_called_once_with(["taskkill", "/F", "/PID", "1234"], shell=False, capture_output=True, text=True)


@pytest.mark.asyncio
async def test_manage_processes_allows_valid_image_name(tool_executor, agent_context, mocker):
    """Ensure manage_processes allows valid process image names."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""
    result = await tool_executor.execute(
        "manage_processes",
        {"action": "kill", "name": "notepad.exe"},
        agent_context
    )
    assert "terminado por orden superior" in result
    mock_run.assert_called_once_with(["taskkill", "/F", "/IM", "notepad.exe*"], shell=False, capture_output=True, text=True)


@pytest.mark.asyncio
async def test_git_operation_allows_valid_subcommand(tool_executor, agent_context, tmp_path, mocker):
    """Ensure git_operation allows approved git subcommands inside workspace."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "On branch main"
    mock_run.return_value.stderr = ""

    result = await tool_executor.execute(
        "git_operation",
        {"operation": "status", "repo_path": str(tmp_path)},
        agent_context
    )
    assert "On branch main" in result
    mock_run.assert_called_once_with(
        ["git", "status"],
        shell=False,
        cwd=str(tmp_path.resolve()),
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.asyncio
async def test_git_operation_rejects_unauthorized_subcommand(tool_executor, agent_context, tmp_path, mocker):
    """Ensure git_operation rejects unauthorized subcommands like push, clone, config."""
    mock_run = mocker.patch("subprocess.run")
    result = await tool_executor.execute(
        "git_operation",
        {"operation": "push origin main", "repo_path": str(tmp_path)},
        agent_context
    )
    assert "no permitida" in result
    mock_run.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dangerous_op",
    [
        "pull --upload-pack='id'",
        "pull --upload-pack=touch /tmp/pwned origin main",
        "status -c alias.status=!id",
        "status --config core.editor=calc",
        "log --output=/tmp/evil",
        "diff --exec-path=/tmp",
        "add --receive-pack=id",
    ],
)
async def test_git_operation_rejects_dangerous_flags(tool_executor, agent_context, tmp_path, mocker, dangerous_op):
    """Ensure git_operation blocks dangerous options capable of arbitrary code execution."""
    mock_run = mocker.patch("subprocess.run")
    result = await tool_executor.execute(
        "git_operation",
        {"operation": dangerous_op, "repo_path": str(tmp_path)},
        agent_context
    )
    assert "peligroso bloqueado" in result
    mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_git_operation_rejects_path_traversal(tool_executor, agent_context, mocker):
    """Ensure git_operation blocks repo_path pointing outside safe base paths."""
    mock_run = mocker.patch("subprocess.run")
    result = await tool_executor.execute(
        "git_operation",
        {"operation": "status", "repo_path": "/etc"},
        agent_context
    )
    assert "Acceso denegado" in result
    mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_execute_shell_legitimate_simple_command(tool_executor, agent_context):
    """Test that a simple legitimate command continues to work without shell"""
    result = await tool_executor.execute(
        "execute_shell",
        {"command": "echo 'hello world'"},
        agent_context
    )
    assert "hello world" in result


@pytest.mark.asyncio
@pytest.mark.parametrize("cmd", [
    "echo hello; id",
    "echo hello ; id",
    "echo hello&& id",
    "echo hello && id",
    "echo hello || id",
    "cat file | grep text",
    "echo `id`",
    "echo $(id)",
    "echo hello > out.txt",
    "cat < /etc/passwd",
])
async def test_execute_shell_rejects_chaining_and_redirection(tool_executor, agent_context, cmd, mocker):
    """Test that commands chained with metacharacters or redirection are rejected without execution"""
    mock_run = mocker.patch("subprocess.run")

    result = await tool_executor.execute(
        "execute_shell",
        {"command": cmd},
        agent_context
    )
    assert "❌ Comando peligroso bloqueado" in result
    mock_run.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("dangerous_cmd", [
    "rm -rf /test",
    "rm -fr /test",
    "rm -r -f /test",
    "rm -f -r /test",
    "rm -R -f /test",
    "rm -rfv /test",
    "rm -vrf /test",
    "rm --recursive --force /test",
    "rm --force --recursive /test",
    "rm -f --recursive /test",
    "rm --force -r /test",
    "shutdown /s /t 0",
    "reboot",
    "format c:",
    "dd if=/dev/zero",
])
async def test_execute_shell_rejects_dangerous_commands_and_rm_variants(tool_executor, agent_context, dangerous_cmd, mocker):
    """Test that dangerous commands and rm -rf variants are blocked without execution"""
    mock_run = mocker.patch("subprocess.run")

    result = await tool_executor.execute(
        "execute_shell",
        {"command": dangerous_cmd},
        agent_context
    )
    assert "❌ Comando peligroso bloqueado" in result
    mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_execute_shell_overdrive_mode_allows_execution(tool_executor, agent_context, mocker):
    """Test that overdrive_mode bypasses shell restrictions"""
    agent_context.overdrive_mode = True
    mock_result = mocker.MagicMock(returncode=0, stdout="overdrive output", stderr="")
    mock_run = mocker.patch("subprocess.run", return_value=mock_result)

    result = await tool_executor.execute(
        "execute_shell",
        {"command": "echo hello; id"},
        agent_context
    )
    assert result == "overdrive output"
    mock_run.assert_called_once()
    assert mock_run.call_args[1]["shell"] is False


@pytest.mark.asyncio
async def test_system_control_uses_subprocess_run(tool_executor, mocker):
    """Test that system_control uses subprocess.run with argument list and shell=False"""
    mock_run = mocker.patch("subprocess.run")

    # shutdown
    res_shutdown = await tool_executor.execute("system_control", {"action": "shutdown"}, None)
    assert "apagado" in res_shutdown.lower()
    mock_run.assert_called_with(
        ["shutdown", "/s", "/t", "60", "/c", "KYNIKOS: Apagado remoto solicitado por Julian"],
        shell=False
    )

    # restart
    res_restart = await tool_executor.execute("system_control", {"action": "restart"}, None)
    assert "reinicio" in res_restart.lower()
    mock_run.assert_called_with(
        ["shutdown", "/r", "/t", "60", "/c", "KYNIKOS: Reinicio remoto solicitado por Julian"],
        shell=False
    )

    # abort
    res_abort = await tool_executor.execute("system_control", {"action": "abort"}, None)
    assert "abortado" in res_abort.lower()
    mock_run.assert_called_with(
        ["shutdown", "/a"],
        shell=False
    )


@pytest.mark.asyncio
async def test_write_and_read_file(tool_executor, agent_context, tmp_path):
    """Test writing and reading a file"""
    # Write file
    write_result = await tool_executor.write_file(
        {"path": "test.txt", "content": "Hello, World!"},
        agent_context
    )
    assert "written" in write_result.lower()
    
    # Read file
    read_result = await tool_executor.read_file(
        {"path": "test.txt"},
        agent_context
    )
    assert "Hello, World!" in read_result


@pytest.mark.asyncio
async def test_list_files_empty(tool_executor, agent_context):
    """Test listing empty directory"""
    result = await tool_executor.list_files(
        {"directory": "."},
        agent_context
    )
    assert "empty" in result.lower() or result == ""


@pytest.mark.asyncio
async def test_tool_not_found(tool_executor, agent_context):
    """Test calling non-existent tool"""
    result = await tool_executor.execute(
        "nonexistent_tool",
        {},
        agent_context
    )
    assert "not found" in result.lower()
