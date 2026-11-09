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


def test_get_sessions(client, tmp_path, monkeypatch):
    """Test get sessions endpoint with sorting and limiting"""
    # Test empty or default state
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Test with simulated sessions directory containing > 50 sessions
    import json
    import os

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True)

    # Create 60 dummy session files with distinct timestamps
    for i in range(60):
        f = sessions_dir / f"session_{i:03d}.jsonl"
        f.write_text(json.dumps({"test": f"session_{i}"}) + "\n", encoding="utf-8")
        # Ensure distinct mtime
        t = 1000000.0 + i * 10
        os.utime(f, (t, t))

    # Also add a .json file
    json_file = sessions_dir / "legacy_session.json"
    json_file.write_text(json.dumps({"test": "legacy"}), encoding="utf-8")
    t_legacy = 1000000.0 + 59 * 10 + 5  # more recent than session 59
    os.utime(json_file, (t_legacy, t_legacy))

    # Temporarily monkeypatch Path in get_sessions by patching the directory check
    import app.cloud.dashboard as dashboard_mod
    monkeypatch.setattr(dashboard_mod, "Path", lambda p: sessions_dir if p == "./data/sessions" else tmp_path / p)

    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) == 50
    # The most recent file should be legacy_session
    assert sessions[0]["session_id"] == "legacy_session"
    assert sessions[1]["session_id"] == "session_059"
