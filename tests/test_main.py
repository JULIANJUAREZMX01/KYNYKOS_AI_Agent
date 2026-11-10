"""Tests for main application"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code in [200, 404]  # 404 if dashboard not found


def test_get_sessions(client):
    """Test get sessions endpoint"""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_sessions_sorted_and_limited(client, tmp_path, monkeypatch):
    """Test get sessions correctly sorts by mtime descending and limits to 50"""
    import os
    import json
    import time

    sessions_dir = tmp_path / "data" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # Create 60 dummy session files with staggered timestamps
    now = time.time()
    for i in range(60):
        file_path = sessions_dir / f"session_{i:02d}.jsonl"
        # Write multiple JSON lines to test tail extraction
        line1 = json.dumps({"step": 1, "session_id": f"session_{i:02d}", "user_id": "test_user"})
        line2 = json.dumps({"step": 2, "session_id": f"session_{i:02d}", "user_id": "test_user", "final": True})
        file_path.write_text(f"{line1}\n{line2}\n", encoding="utf-8")
        # Give staggered mtimes: session_59 is newest, session_00 is oldest
        file_mtime = now - (60 - i) * 10
        os.utime(file_path, (file_mtime, file_mtime))

    # Also add a regular .json file
    json_file = sessions_dir / "session_special.json"
    json_file.write_text(json.dumps({"session_id": "session_special", "user_id": "special_user"}), encoding="utf-8")
    special_mtime = now + 10  # Brand new
    os.utime(json_file, (special_mtime, special_mtime))

    # Monkeypatch the sessions directory in dashboard route to use our test dir
    monkeypatch.chdir(tmp_path)

    response = client.get("/api/sessions")
    assert response.status_code == 200
    sessions = response.json()

    # Must be capped at 50
    assert len(sessions) == 50

    # Newest file (session_special) must be first
    assert sessions[0]["session_id"] == "session_special"

    # Second newest must be session_59, verifying descending mtime sort
    assert sessions[1]["session_id"] == "session_59"
    assert sessions[1]["final"] is True

    # Check timestamps are sorted descending
    mtimes = [s["last_modified"] for s in sessions]
    assert mtimes == sorted(mtimes, reverse=True)
