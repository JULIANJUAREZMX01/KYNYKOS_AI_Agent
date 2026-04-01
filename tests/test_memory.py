import sys
from unittest.mock import MagicMock

# Mock loguru
mock_loguru = MagicMock()
sys.modules["loguru"] = mock_loguru

import pytest
import json
import asyncio
from pathlib import Path
from app.core.memory import Memory

@pytest.fixture
def memory_manager(tmp_path):
    """Fixture for Memory manager with temporary workspace"""
    return Memory(tmp_path)

def test_memory_init_creates_directory(tmp_path):
    """Test that __init__ creates the memory directory"""
    memory_path = tmp_path / "memory"
    assert not memory_path.exists()

    Memory(tmp_path)
    assert memory_path.exists()
    assert memory_path.is_dir()

def test_load_empty_memory(memory_manager):
    """Test loading memory when file does not exist"""
    assert memory_manager.load() == {}

def test_load_existing_memory(memory_manager, tmp_path):
    """Test loading memory when file exists"""
    content = "# Test Memory\nSome content here."
    memory_file = tmp_path / "memory" / "MEMORY.md"
    memory_file.write_text(content, encoding="utf-8")

    result = memory_manager.load()
    assert result == {"raw": content}

def test_save_memory(memory_manager, tmp_path):
    """Test saving memory to MEMORY.md"""
    content = "Saved memory content"
    memory_manager.save(content)

    memory_file = tmp_path / "memory" / "MEMORY.md"
    assert memory_file.exists()
    assert memory_file.read_text(encoding="utf-8") == content

def test_get_memory_context_empty(memory_manager):
    """Test get_memory_context when file does not exist"""
    assert memory_manager.get_memory_context() == ""

def test_get_memory_context_exists(memory_manager, tmp_path):
    """Test get_memory_context when file exists"""
    content = "Context content"
    memory_file = tmp_path / "memory" / "MEMORY.md"
    memory_file.write_text(content, encoding="utf-8")

    assert memory_manager.get_memory_context() == content

def test_append_session(memory_manager, tmp_path):
    """Test appending messages to a session JSONL file"""
    session_id = "test_session"

    # Custom class with to_dict method
    class MockMessage:
        def to_dict(self):
            return {"role": "assistant", "content": "hello"}

    messages = [
        {"role": "user", "content": "hi"},
        MockMessage(),
        "plain string" # Will be serialized as is
    ]

    asyncio.run(memory_manager.append_session(session_id, messages))

    session_file = tmp_path / "data" / "sessions" / f"{session_id}.jsonl"
    assert session_file.exists()

    lines = session_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3

    assert json.loads(lines[0]) == {"role": "user", "content": "hi"}
    assert json.loads(lines[1]) == {"role": "assistant", "content": "hello"}
    assert json.loads(lines[2]) == "plain string"

def test_append_session_to_existing_file(memory_manager, tmp_path):
    """Test appending to an existing session file"""
    session_id = "existing_session"
    sessions_dir = tmp_path / "data" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    session_file = sessions_dir / f"{session_id}.jsonl"

    session_file.write_text(json.dumps({"msg": "initial"}) + "\n", encoding="utf-8")

    asyncio.run(memory_manager.append_session(session_id, [{"msg": "new"}]))

    lines = session_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"msg": "initial"}
    assert json.loads(lines[1]) == {"msg": "new"}
