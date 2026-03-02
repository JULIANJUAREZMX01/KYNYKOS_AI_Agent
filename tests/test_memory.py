"""Tests for Memory class"""

import json
import asyncio
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock loguru before importing app.core.memory
mock_loguru = MagicMock()
sys.modules["loguru"] = mock_loguru

from app.core.memory import Memory

@pytest.fixture
def memory(tmp_path):
    """Fixture for Memory class with temporary workspace"""
    return Memory(tmp_path)

def test_memory_initialization(tmp_path):
    """Test Memory initialization and directory creation"""
    workspace = tmp_path / "test_workspace"
    memory_obj = Memory(workspace)

    assert memory_obj.workspace_path == workspace
    assert memory_obj.memory_file == workspace / "memory" / "MEMORY.md"
    assert (workspace / "memory").exists()

def test_load_non_existent_file(memory):
    """Test load() when file does not exist"""
    # memory_file is created as part of __init__ parent directory,
    # but the file itself doesn't exist yet.
    if memory.memory_file.exists():
        memory.memory_file.unlink()

    result = memory.load()
    assert result == {}

def test_load_existing_file(memory):
    """Test load() when file exists"""
    content = "Test memory content"
    memory.memory_file.write_text(content, encoding="utf-8")

    result = memory.load()
    assert result == {"raw": content}

def test_load_exception(memory):
    """Test load() when an exception occurs"""
    with patch.object(Path, 'exists', side_effect=Exception("Test error")):
        result = memory.load()
        assert result == {}

def test_save(memory):
    """Test save() functionality"""
    content = "New memory content"
    memory.save(content)

    assert memory.memory_file.read_text(encoding="utf-8") == content

def test_save_exception(memory):
    """Test save() when an exception occurs"""
    with patch.object(Path, 'write_text', side_effect=Exception("Test error")):
        # Should not raise exception, just log it
        memory.save("content")

def test_append_session_plain_dict(memory):
    """Test append_session() with plain dictionary messages"""
    session_id = "test_session_1"
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"}
    ]

    asyncio.run(memory.append_session(session_id, messages))

    session_file = memory.workspace_path / "data" / "sessions" / f"{session_id}.jsonl"
    assert session_file.exists()

    with open(session_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0]) == messages[0]
        assert json.loads(lines[1]) == messages[1]

def test_append_session_with_to_dict(memory):
    """Test append_session() with objects having to_dict()"""
    class MockMessage:
        def __init__(self, data):
            self.data = data
        def to_dict(self):
            return self.data

    session_id = "test_session_2"
    messages = [MockMessage({"role": "user", "content": "test"})]

    asyncio.run(memory.append_session(session_id, messages))

    session_file = memory.workspace_path / "data" / "sessions" / f"{session_id}.jsonl"
    with open(session_file, "r", encoding="utf-8") as f:
        line = f.readline()
        assert json.loads(line) == {"role": "user", "content": "test"}

def test_append_session_serialization_error(memory):
    """Test append_session() when message serialization fails"""
    session_id = "test_session_3"
    # Unserializable object
    messages = [{"data": object()}]

    asyncio.run(memory.append_session(session_id, messages))

    session_file = memory.workspace_path / "data" / "sessions" / f"{session_id}.jsonl"
    with open(session_file, "r", encoding="utf-8") as f:
        assert f.read() == ""

def test_append_session_exception(memory):
    """Test append_session() when a general exception occurs"""
    with patch("app.core.memory.logger") as mock_logger:
        with patch.object(Path, 'mkdir', side_effect=Exception("Disk full")):
            asyncio.run(memory.append_session("fail", [{"msg": "test"}]))
            mock_logger.error.assert_called()

def test_get_memory_context(memory):
    """Test get_memory_context()"""
    # Case 1: File doesn't exist
    if memory.memory_file.exists():
        memory.memory_file.unlink()
    assert memory.get_memory_context() == ""

    # Case 2: File exists
    content = "Context content"
    memory.memory_file.write_text(content, encoding="utf-8")
    assert memory.get_memory_context() == content

def test_get_memory_context_exception(memory):
    """Test get_memory_context() when an exception occurs"""
    with patch.object(Path, 'exists', side_effect=Exception("Test error")):
        assert memory.get_memory_context() == ""
