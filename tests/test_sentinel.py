import sys
import os
from unittest.mock import MagicMock
from pathlib import Path
import pytest

# Minimal mocking to allow imports in the sandbox environment
# We use a context manager style to keep it as localized as possible
# or just do it once if we know we are in the sandbox.

def setup_mocks():
    if "pydantic" not in sys.modules:
        mock_pydantic = MagicMock()
        mock_pydantic_settings = MagicMock()
        class MockBaseSettings:
            def __init__(self, **kwargs): pass
            class Config: pass
        mock_pydantic_settings.BaseSettings = MockBaseSettings
        sys.modules["pydantic"] = mock_pydantic
        sys.modules["pydantic_settings"] = mock_pydantic_settings

    if "loguru" not in sys.modules:
        sys.modules["loguru"] = MagicMock()

    if "aiofiles" not in sys.modules:
        sys.modules["aiofiles"] = MagicMock()

setup_mocks()

from app.core.sentinel import LogSentinel

# Mock ContractSettings and Settings
class MockContractSettings:
    def __init__(self):
        self.sentinel_enabled = False
        self.log_check_interval = 60
        self.alert_on_failure = True
        self.auto_healing_enabled = False

class MockSettings:
    def __init__(self):
        self.contract_settings = MockContractSettings()

@pytest.fixture
def sentinel(tmp_path, monkeypatch):
    # Change working directory to tmp_path to isolate all file operations
    monkeypatch.chdir(tmp_path)

    # Ensure logs directory exists for the default watch
    (tmp_path / "logs").mkdir()

    settings = MockSettings()
    return LogSentinel(settings)

def test_add_watch_existing_file(sentinel, tmp_path):
    log_file = tmp_path / "test.log"
    content = "line1\nline2\n"
    log_file.write_text(content)

    sentinel.add_watch(str(log_file))

    resolved_path = str(log_file.resolve())
    assert resolved_path in sentinel.watch_list
    assert sentinel.watch_list[resolved_path] == len(content)

def test_add_watch_non_existent_file(sentinel, tmp_path):
    log_file = tmp_path / "new.log"
    # Should be already gone if tmp_path is fresh, but just in case
    if log_file.exists():
        log_file.unlink()

    sentinel.add_watch(str(log_file))

    assert log_file.exists()
    resolved_path = str(log_file.resolve())
    assert resolved_path in sentinel.watch_list
    assert sentinel.watch_list[resolved_path] == 0

def test_add_watch_non_existent_directory(sentinel, tmp_path):
    log_dir = tmp_path / "nested" / "dir"
    log_file = log_dir / "deep.log"

    sentinel.add_watch(str(log_file))

    assert log_dir.exists()
    assert log_file.exists()
    resolved_path = str(log_file.resolve())
    assert resolved_path in sentinel.watch_list
    assert sentinel.watch_list[resolved_path] == 0

def test_add_watch_directory_instead_of_file(sentinel, tmp_path):
    log_dir = tmp_path / "is_a_dir"
    log_dir.mkdir()

    sentinel.add_watch(str(log_dir))

    resolved_path = str(log_dir.resolve())
    assert resolved_path not in sentinel.watch_list

def test_add_watch_error_handling(sentinel, monkeypatch):
    # Mock Path.resolve to raise an exception
    def mock_resolve(self):
        raise OSError("Simulated error")

    monkeypatch.setattr(Path, "resolve", mock_resolve)

    # This should not raise an exception because of the try-except in add_watch
    sentinel.add_watch("any_file.log")
    assert len(sentinel.watch_list) == 1 # Only the default one from __init__ (if it didn't fail)
