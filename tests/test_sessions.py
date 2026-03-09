import pytest
import json
import os
import time
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from app.cloud.sessions import SessionManager
from app.core.context import AgentContext

@pytest.fixture
def session_manager(tmp_path):
    return SessionManager(data_dir=str(tmp_path))

@pytest.fixture
def agent_context():
    ctx = AgentContext(
        session_id="test_session_123",
        user_id="user_456",
        channel="telegram"
    )
    ctx.add_message("user", "Hello")
    ctx.add_message("assistant", "Hi there!")
    return ctx

def test_session_manager_init(tmp_path):
    data_dir = tmp_path / "data"
    manager = SessionManager(data_dir=str(data_dir))
    assert manager.sessions_dir.exists()
    assert manager.sessions_dir.is_dir()

def test_save_session(session_manager, agent_context):
    success = asyncio.run(session_manager.save_session(agent_context))
    assert success is True

    session_file = session_manager.sessions_dir / f"{agent_context.session_id}.jsonl"
    assert session_file.exists()

    with open(session_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["session_id"] == agent_context.session_id
        assert len(data["messages"]) == 2

def test_load_session(session_manager, agent_context):
    asyncio.run(session_manager.save_session(agent_context))

    loaded_ctx = asyncio.run(session_manager.load_session(agent_context.session_id))
    assert loaded_ctx is not None
    assert loaded_ctx.session_id == agent_context.session_id
    assert loaded_ctx.user_id == agent_context.user_id
    assert loaded_ctx.channel == agent_context.channel
    assert len(loaded_ctx.messages) == 2
    assert loaded_ctx.messages[0].role == "user"
    assert loaded_ctx.messages[0].content == "Hello"
    assert loaded_ctx.messages[1].role == "assistant"
    assert loaded_ctx.messages[1].content == "Hi there!"

def test_load_nonexistent_session(session_manager):
    loaded_ctx = asyncio.run(session_manager.load_session("nonexistent"))
    assert loaded_ctx is None

def test_list_sessions(session_manager):
    ctx1 = AgentContext(session_id="s1", user_id="u1", channel="c1")
    ctx2 = AgentContext(session_id="s2", user_id="u2", channel="c2")

    asyncio.run(session_manager.save_session(ctx1))
    asyncio.run(session_manager.save_session(ctx2))

    # Ensure ctx2 has a newer mtime
    file1 = session_manager.sessions_dir / "s1.jsonl"
    file2 = session_manager.sessions_dir / "s2.jsonl"

    old_time = time.time() - 10
    new_time = time.time()

    os.utime(file1, (old_time, old_time))
    os.utime(file2, (new_time, new_time))

    sessions = asyncio.run(session_manager.list_sessions())
    assert len(sessions) == 2
    # ctx2 should be first because it's more recent
    assert sessions[0]["session_id"] == "s2"
    assert sessions[1]["session_id"] == "s1"
    assert sessions[0]["user_id"] == "u2"

def test_cleanup_old_sessions(session_manager):
    ctx_old = AgentContext(session_id="old_session", user_id="u1", channel="c1")
    ctx_new = AgentContext(session_id="new_session", user_id="u2", channel="c2")

    asyncio.run(session_manager.save_session(ctx_old))
    asyncio.run(session_manager.save_session(ctx_new))

    old_file = session_manager.sessions_dir / "old_session.jsonl"
    # Set mtime to 40 days ago
    old_time = (datetime.now() - timedelta(days=40)).timestamp()
    os.utime(old_file, (old_time, old_time))

    deleted_count = asyncio.run(session_manager.cleanup_old_sessions(days=30))
    assert deleted_count == 1
    assert not old_file.exists()
    assert (session_manager.sessions_dir / "new_session.jsonl").exists()

def test_export_session_json(session_manager, agent_context):
    asyncio.run(session_manager.save_session(agent_context))
    # Add another message to the same session
    agent_context.add_message("user", "Another one")
    asyncio.run(session_manager.save_session(agent_context))

    json_export = asyncio.run(session_manager.export_session(agent_context.session_id, format="json"))
    assert json_export is not None
    data = json.loads(json_export)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["session_id"] == agent_context.session_id

def test_export_session_csv(session_manager, agent_context):
    asyncio.run(session_manager.save_session(agent_context))

    csv_export = asyncio.run(session_manager.export_session(agent_context.session_id, format="csv"))
    assert csv_export is not None
    assert "timestamp,role,content" in csv_export
    assert "user,Hello" in csv_export
    assert "assistant,Hi there!" in csv_export

def test_export_invalid_format(session_manager, agent_context):
    asyncio.run(session_manager.save_session(agent_context))
    result = asyncio.run(session_manager.export_session(agent_context.session_id, format="xml"))
    assert result is None

def test_corrupted_session_file(session_manager):
    session_id = "corrupted"
    session_file = session_manager.sessions_dir / f"{session_id}.jsonl"
    with open(session_file, "w") as f:
        f.write("invalid json\n")

    # load_session should handle it gracefully
    loaded_ctx = asyncio.run(session_manager.load_session(session_id))
    assert loaded_ctx is None

    # list_sessions should skip it
    sessions = asyncio.run(session_manager.list_sessions())
    assert len(sessions) == 0
