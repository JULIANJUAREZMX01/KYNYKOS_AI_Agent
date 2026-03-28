import sys
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

# Mock missing dependencies
mock_fastapi = MagicMock()
mock_loguru = MagicMock()
mock_utils = MagicMock()

sys.modules["fastapi"] = mock_fastapi
sys.modules["loguru"] = mock_loguru
sys.modules["app.utils"] = mock_utils

# Mock APIRouter
class MockRouter:
    def __init__(self, *args, **kwargs):
        self.routes = []

    def get(self, path):
        def decorator(func):
            self.routes.append(("GET", path, func))
            return func
        return decorator

    def post(self, path):
        def decorator(func):
            self.routes.append(("POST", path, func))
            return func
        return decorator

mock_fastapi.APIRouter = MockRouter

import pytest
from app.cloud.dashboard import create_dashboard_routes

@pytest.fixture
def dashboard_handlers():
    router = create_dashboard_routes()
    handlers = {f"{method} {path}": func for method, path, func in router.routes}
    return handlers

def test_get_sessions_empty(dashboard_handlers):
    get_sessions = dashboard_handlers["GET /sessions"]

    async def run():
        with patch("app.cloud.dashboard.Path") as MockPath:
            mock_dir = MockPath.return_value
            mock_dir.exists.return_value = False

            result = await get_sessions()
            assert result == []

    asyncio.run(run())

def test_get_sessions_with_files(dashboard_handlers):
    get_sessions = dashboard_handlers["GET /sessions"]

    async def run():
        with patch("app.cloud.dashboard.Path") as MockPath, \
             patch("os.path.getmtime") as mock_mtime:

            mock_dir = MockPath.return_value
            mock_dir.exists.return_value = True

            file1 = MagicMock(spec=Path)
            file1.suffix = ".json"
            file1.stem = "session1"
            file1.read_text.return_value = json.dumps({"data": "session1_content"})

            file2 = MagicMock(spec=Path)
            file2.suffix = ".jsonl"
            file2.stem = "session2"
            file2.read_text.return_value = '{"data": "old"}\n{"data": "session2_content"}'

            mock_dir.glob.side_effect = lambda pattern: [file1] if "json" in pattern and "jsonl" not in pattern else ([file2] if "jsonl" in pattern else [])

            mock_mtime.side_effect = lambda f: 100 if f.stem == "session1" else 200

            result = await get_sessions()

            assert len(result) == 2
            assert result[0]["session_id"] == "session2"  # Sorted by mtime reverse
            assert result[0]["data"] == "session2_content"
            assert result[1]["session_id"] == "session1"
            assert result[1]["data"] == "session1_content"

    asyncio.run(run())

def test_get_memory(dashboard_handlers):
    get_memory = dashboard_handlers["GET /memory"]

    async def run():
        with patch("app.cloud.dashboard.Path") as MockPath:
            mock_file = MockPath.return_value

            # Test exists
            mock_file.exists.return_value = True
            mock_file.read_text.return_value = "Memory content"
            result = await get_memory()
            assert result == {"content": "Memory content"}

            # Test not exists
            mock_file.exists.return_value = False
            result = await get_memory()
            assert "not found" in result["content"]

    asyncio.run(run())

def test_update_memory(dashboard_handlers):
    update_memory = dashboard_handlers["POST /memory"]

    async def run():
        with patch("app.cloud.dashboard.Path") as MockPath:
            mock_file = MockPath.return_value

            result = await update_memory({"content": "New memory"})

            assert result == {"success": True}
            mock_file.parent.mkdir.assert_called_with(parents=True, exist_ok=True)
            mock_file.write_text.assert_called_with("New memory", encoding="utf-8")

    asyncio.run(run())

def test_get_skills(dashboard_handlers):
    get_skills = dashboard_handlers["GET /skills"]

    async def run():
        with patch("app.cloud.dashboard.Path") as MockPath:
            mock_dir = MockPath.return_value
            mock_dir.exists.return_value = True

            skill_dir = MagicMock(spec=Path)
            skill_dir.is_dir.return_value = True
            skill_dir.name = "test_skill"

            skill_md = MagicMock(spec=Path)
            skill_md.exists.return_value = True
            skill_md.read_text.return_value = "Skill content"

            skill_dir.__truediv__.return_value = skill_md

            mock_dir.iterdir.return_value = [skill_dir]

            result = await get_skills()

            assert len(result) == 1
            assert result[0]["name"] == "test_skill"
            assert result[0]["content"] == "Skill content"

    asyncio.run(run())

def test_get_logs(dashboard_handlers):
    get_logs = dashboard_handlers["GET /logs"]

    async def run():
        result = await get_logs()
        assert "logs" in result
        assert "message" in result
        assert "Render Dashboard" in result["message"]

    asyncio.run(run())
