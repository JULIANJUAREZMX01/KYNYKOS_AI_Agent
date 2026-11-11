"""Tests for dashboard functionality and session reading optimization"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.cloud.dashboard import _read_last_line_from_file
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_read_last_line_from_file(tmp_path: Path):
    """Test reading the last line under various file scenarios"""
    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("", encoding="utf-8")
    assert _read_last_line_from_file(empty_file) == ""

    single_line_file = tmp_path / "single.jsonl"
    single_line_file.write_text('{"msg": "hello"}\n', encoding="utf-8")
    assert _read_last_line_from_file(single_line_file) == '{"msg": "hello"}'

    trailing_newlines_file = tmp_path / "trailing.jsonl"
    trailing_newlines_file.write_text('{"msg": "first"}\n{"msg": "last"}\n\n\n', encoding="utf-8")
    assert _read_last_line_from_file(trailing_newlines_file) == '{"msg": "last"}'

    # Multi-line large file exceeding standard buffer size (e.g. > 4KB)
    large_file = tmp_path / "large.jsonl"
    with open(large_file, "w", encoding="utf-8") as f:
        for i in range(100):
            f.write(json.dumps({"line": i, "payload": "x" * 50}) + "\n")
        # Ensure the last line itself is larger than the buffer size (e.g. 5KB line with 128B buffer)
        huge_payload = "A" * 5000
        f.write(json.dumps({"line": 999, "status": "final_state", "data": huge_payload}) + "\n")

    last = _read_last_line_from_file(large_file, buffer_size=128)
    data = json.loads(last)
    assert data["line"] == 999
    assert data["status"] == "final_state"
    assert data["data"] == huge_payload

    # Single-line huge file that exceeds buffer size with no previous newline
    single_huge = tmp_path / "single_huge.jsonl"
    single_huge.write_text(json.dumps({"line": 1, "data": "B" * 5000}) + "\n", encoding="utf-8")
    last_single = _read_last_line_from_file(single_huge, buffer_size=128)
    data_single = json.loads(last_single)
    assert data_single["line"] == 1
    assert data_single["data"] == "B" * 5000


def test_get_sessions_with_json_and_jsonl(tmp_path: Path, monkeypatch, client):
    """Test get_sessions endpoint with both json and jsonl files"""
    sessions_dir = tmp_path / "data" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # Mock Path("./data/sessions") in dashboard
    original_path = Path

    def mocked_path(arg, *args, **kwargs):
        if str(arg) == "./data/sessions":
            return sessions_dir
        return original_path(arg, *args, **kwargs)

    monkeypatch.setattr("app.cloud.dashboard.Path", mocked_path)

    # 1. Add standard json session
    json_session = sessions_dir / "session1.json"
    json_session.write_text(json.dumps({
        "user_id": "user_a",
        "channel": "telegram",
        "data": "state1"
    }), encoding="utf-8")

    # 2. Add jsonl session with history
    jsonl_session = sessions_dir / "session2.jsonl"
    with open(jsonl_session, "w", encoding="utf-8") as f:
        f.write(json.dumps({"user_id": "user_b", "channel": "whatsapp", "data": "initial"}) + "\n")
        f.write(json.dumps({"user_id": "user_b", "channel": "whatsapp", "data": "updated"}) + "\n")

    response = client.get("/api/sessions")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2

    # Map by session_id
    sessions_by_id = {s["session_id"]: s for s in results}
    assert "session1" in sessions_by_id
    assert sessions_by_id["session1"]["user_id"] == "user_a"
    assert sessions_by_id["session1"]["data"] == "state1"

    assert "session2" in sessions_by_id
    assert sessions_by_id["session2"]["user_id"] == "user_b"
    assert sessions_by_id["session2"]["data"] == "updated"
