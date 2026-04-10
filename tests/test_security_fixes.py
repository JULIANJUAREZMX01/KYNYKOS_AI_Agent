import sys
from unittest.mock import MagicMock, patch

# Mock loguru
mock_loguru = MagicMock()
sys.modules["loguru"] = mock_loguru

import asyncio
import shlex
from app.core.tools import ToolExecutor
from app.core.context import AgentContext

async def test_execute_shell_no_injection(tool_executor, agent_context):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="hello", stderr="")

        injection = "echo hello; echo vulnerable"
        await tool_executor.execute("execute_shell", {"command": injection}, agent_context)

        assert mock_run.called
        args, kwargs = mock_run.call_args
        assert kwargs["shell"] is False
        assert args[0] == ["echo", "hello;", "echo", "vulnerable"]
        print("✓ test_execute_shell_no_injection passed")

async def test_git_operation_no_injection(tool_executor, agent_context):
    # git_operation takes args as a dict, no context
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="switched", stderr="")

        # Use a safe operation like 'status'
        operation = "status; echo vulnerable"
        await tool_executor.execute("git_operation", {"operation": operation, "repo_path": "/tmp"}, agent_context)

        assert mock_run.called
        args, kwargs = mock_run.call_args
        assert kwargs["shell"] is False
        assert kwargs["cwd"] == "/tmp"
        assert args[0] == ["git", "status;", "echo", "vulnerable"]
        print("✓ test_git_operation_no_injection passed")

async def test_search_code_no_injection(tool_executor, agent_context):
    # search_code takes args as a dict, no context
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="found", stderr="")

        query = "pattern'; echo vulnerable"
        await tool_executor.execute("search_code", {"query": query, "path": "C:\\test"}, agent_context)

        assert mock_run.called
        args, kwargs = mock_run.call_args
        assert kwargs["shell"] is False
        cmd = args[0]
        assert cmd[0] == "powershell"
        # The query should be passed as a separate argument, not part of the command string directly
        assert cmd[-1] == query
        print("✓ test_search_code_no_injection passed")

async def run_manual():
    executor = ToolExecutor()
    ctx = AgentContext(session_id="test", user_id="test", channel="test")
    print("Running manual verification...")
    await test_execute_shell_no_injection(executor, ctx)
    await test_git_operation_no_injection(executor, ctx)
    await test_search_code_no_injection(executor, ctx)
    print("Manual verification passed!")

if __name__ == "__main__":
    asyncio.run(run_manual())
