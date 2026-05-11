import pytest
import json
import os
from pathlib import Path
from app.cloud.mcp_server import list_sessions

def test_list_sessions_no_dir(monkeypatch, tmp_path):
    """Test list_sessions when the sessions directory does not exist."""
    monkeypatch.chdir(tmp_path)
    # Ensure ./data/sessions doesn't exist
    assert not Path("./data/sessions").exists()

    result = list_sessions()
    assert result == {"sessions": []}

def test_list_sessions_empty_dir(monkeypatch, tmp_path):
    """Test list_sessions when the sessions directory is empty."""
    monkeypatch.chdir(tmp_path)
    sessions_dir = Path("./data/sessions")
    sessions_dir.mkdir(parents=True)

    result = list_sessions()
    assert result == {"sessions": []}

def test_list_sessions_valid_files(monkeypatch, tmp_path):
    """Test list_sessions with valid .jsonl files."""
    monkeypatch.chdir(tmp_path)
    sessions_dir = Path("./data/sessions")
    sessions_dir.mkdir(parents=True)

    data1 = {"id": "1", "msg": "hello"}
    data2 = {"id": "2", "msg": "world"}

    s1 = sessions_dir / "session1.jsonl"
    s1.write_text(json.dumps(data1) + "\n", encoding="utf-8")

    # Ensure s2 has a later mtime
    s2 = sessions_dir / "session2.jsonl"
    s2.write_text(json.dumps(data2) + "\n", encoding="utf-8")
    os.utime(s2, (os.path.getatime(s2), os.path.getmtime(s2) + 100))

    result = list_sessions()
    assert "sessions" in result
    assert len(result["sessions"]) == 2
    # Should be sorted by mtime descending, so s2 first
    assert result["sessions"][0] == data2
    assert result["sessions"][1] == data1

def test_list_sessions_invalid_json(monkeypatch, tmp_path):
    """Test list_sessions skips invalid JSON lines."""
    monkeypatch.chdir(tmp_path)
    sessions_dir = Path("./data/sessions")
    sessions_dir.mkdir(parents=True)

    s1 = sessions_dir / "session1.jsonl"
    s1.write_text("invalid json\n" + json.dumps({"id": "1"}) + "\n", encoding="utf-8")

    result = list_sessions()
    assert len(result["sessions"]) == 1
    assert result["sessions"][0]["id"] == "1"

def test_list_sessions_limit(monkeypatch, tmp_path):
    """Test list_sessions respects the limit parameter."""
    monkeypatch.chdir(tmp_path)
    sessions_dir = Path("./data/sessions")
    sessions_dir.mkdir(parents=True)

    for i in range(10):
        f = sessions_dir / f"session{i}.jsonl"
        f.write_text(json.dumps({"id": str(i)}) + "\n", encoding="utf-8")
        # Ensure different mtimes
        os.utime(f, (os.path.getatime(f), os.path.getmtime(f) + i))

    # Limit to 5 most recent
    result = list_sessions(limit=5)
    assert len(result["sessions"]) == 5
    # Should be 9, 8, 7, 6, 5
    assert result["sessions"][0]["id"] == "9"
    assert result["sessions"][4]["id"] == "5"

def test_list_sessions_multiple_lines_per_file(monkeypatch, tmp_path):
    """Test list_sessions with multiple JSON lines in a single file."""
    monkeypatch.chdir(tmp_path)
    sessions_dir = Path("./data/sessions")
    sessions_dir.mkdir(parents=True)

    s1 = sessions_dir / "session1.jsonl"
    lines = [
        json.dumps({"step": 1}),
        json.dumps({"step": 2}),
        json.dumps({"step": 3})
    ]
    s1.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = list_sessions()
    assert len(result["sessions"]) == 3
    assert result["sessions"][0]["step"] == 1
    assert result["sessions"][1]["step"] == 2
    assert result["sessions"][2]["step"] == 3
