import pytest
import json
from pathlib import Path
from app.cloud.sessions import SessionManager
from app.core.context import AgentContext

@pytest.fixture
def session_manager(tmp_path):
    """SessionManager instance with a temporary data directory"""
    return SessionManager(data_dir=str(tmp_path))

@pytest.fixture
def sample_session_id():
    return "test_session_123"

@pytest.fixture
async def sample_context(sample_session_id):
    ctx = AgentContext(
        session_id=sample_session_id,
        user_id="test_user",
        channel="test_channel"
    )
    ctx.add_message("user", "Hello")
    ctx.add_message("assistant", "Hi there! This is a long message that should be truncated in CSV export to see if it works correctly.")
    return ctx

@pytest.mark.asyncio
async def test_export_session_json(session_manager, sample_context, sample_session_id):
    """Test exporting session to JSON format"""
    # Save the session first
    await session_manager.save_session(sample_context)

    # Export to JSON
    json_output = await session_manager.export_session(sample_session_id, format="json")

    assert json_output is not None
    data = json.loads(json_output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["session_id"] == sample_session_id
    assert len(data[0]["messages"]) == 2

@pytest.mark.asyncio
async def test_export_session_csv(session_manager, sample_context, sample_session_id):
    """Test exporting session to CSV format"""
    # Save the session first
    await session_manager.save_session(sample_context)

    # Export to CSV
    csv_output = await session_manager.export_session(sample_session_id, format="csv")

    assert csv_output is not None
    lines = csv_output.strip().split("\r\n")

    # Verify headers
    assert lines[0] == "timestamp,role,content"

    # Verify content (one line for each message)
    assert len(lines) == 3 # 1 header + 2 messages

    # Verify truncation (the second message is long)
    assert "Hi there! This is a long message" in lines[2]
    assert len(lines[2].split(",")[2]) <= 100

@pytest.mark.asyncio
async def test_export_session_not_found(session_manager):
    """Test exporting a session that does not exist"""
    result = await session_manager.export_session("non_existent_id")
    assert result is None

@pytest.mark.asyncio
async def test_export_session_invalid_format(session_manager, sample_context, sample_session_id):
    """Test exporting a session with an invalid format"""
    await session_manager.save_session(sample_context)
    result = await session_manager.export_session(sample_session_id, format="xml")
    assert result is None
