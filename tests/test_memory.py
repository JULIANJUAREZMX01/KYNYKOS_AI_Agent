import pytest
import json
from pathlib import Path
from app.core.memory import Memory

@pytest.fixture
def memory(tmp_path):
    return Memory(workspace_path=tmp_path)

@pytest.mark.asyncio
async def test_memory_append_session(memory, tmp_path):
    session_id = "test_session"
    messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]

    await memory.append_session(session_id, messages)

    session_file = tmp_path / "data" / "sessions" / f"{session_id}.jsonl"
    assert session_file.exists()

    lines = session_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == messages[0]
    assert json.loads(lines[1]) == messages[1]

@pytest.mark.asyncio
async def test_memory_save_load(memory, tmp_path):
    content = "Test memory content"
    await memory.save(content)

    loaded = await memory.load()
    assert loaded["raw"] == content

    context = await memory.get_memory_context()
    assert context == content

@pytest.mark.asyncio
async def test_memory_load_empty(memory):
    assert await memory.load() == {}
    assert await memory.get_memory_context() == ""
