"""Tests for tool executor"""

import pytest
import sys
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
async def test_git_operation_legitimate_command(tool_executor, mocker):
    """Test that safe git operations execute with argument list and shell=False"""
    mock_result = mocker.MagicMock(returncode=0, stdout="On branch main\n", stderr="")
    mock_run = mocker.patch("subprocess.run", return_value=mock_result)

    result = await tool_executor.execute(
        "git_operation",
        {"operation": "status --short", "repo_path": "/fake/repo"},
        None
    )
    assert "On branch main" in result
    mock_run.assert_called_once_with(
        ["git", "status", "--short"],
        shell=False,
        cwd="/fake/repo",
        capture_output=True,
        text=True,
        timeout=30
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", [
    "checkout main",
    "push origin main",
    "clone https://github.com/evil/repo",
    "reset --hard HEAD~1",
    "clean -fdx",
])
async def test_git_operation_rejects_disallowed_subcommands(tool_executor, operation, mocker):
    """Test that non-whitelisted git subcommands are rejected without running git"""
    mock_run = mocker.patch("subprocess.run")

    result = await tool_executor.execute(
        "git_operation",
        {"operation": operation},
        None
    )
    assert "❌ Subcomando git no permitido" in result
    mock_run.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", [
    "status --upload-pack=touch /tmp/pwned",
    "status --receive-pack=evil",
    "log --exec-path=/tmp",
    "status -c core.editor=calc",
    "diff --config core.editor=calc",
])
async def test_git_operation_rejects_dangerous_flags(tool_executor, operation, mocker):
    """Test that dangerous options/flags are blocked for safe subcommands"""
    mock_run = mocker.patch("subprocess.run")

    result = await tool_executor.execute(
        "git_operation",
        {"operation": operation},
        None
    )
    assert "❌ Opción de git no permitida por seguridad" in result
    mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_self_repair_uses_argument_lists_without_shell(tool_executor, mocker):
    """Test that self_repair runs commands as lists with shell=False"""
    mock_result = mocker.MagicMock(returncode=0, stdout="OK", stderr="")
    mock_run = mocker.patch("subprocess.run", return_value=mock_result)
    mocker.patch.object(tool_executor, "_rebuild_index", return_value="reindexed")

    result = await tool_executor.execute(
        "self_repair",
        {"target": "all"},
        None
    )
    assert "Auto-Reparación Completada" in result

    # Check subprocess calls
    assert mock_run.call_count == 2
    first_call = mock_run.call_args_list[0]
    second_call = mock_run.call_args_list[1]

    assert first_call[0][0] == ["git", "pull", "origin", "main"]
    assert first_call[1]["shell"] is False

    assert second_call[0][0] == [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    assert second_call[1]["shell"] is False


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
