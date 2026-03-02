import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Minimal mocking to allow imports in environments without all dependencies
# This handles the missing 'loguru' and other packages while keeping tests focused
MOCK_MODULES = ['loguru', 'yaml', 'pydantic', 'pydantic_settings']
for mod in MOCK_MODULES:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

# Import the class after mocking its module-level dependencies
from app.core.sentinel import LogSentinel

@pytest.fixture
def mock_settings():
    """Mock application settings for testing"""
    settings = MagicMock()
    settings.contract_settings.log_check_interval = 5
    settings.contract_settings.sentinel_enabled = True
    settings.contract_settings.alert_on_failure = True
    settings.contract_settings.auto_healing_enabled = True
    return settings

@pytest.fixture
def sentinel(mock_settings):
    """Fixture to create a LogSentinel instance with mocked dependencies"""
    # Patch get_logger to avoid loguru dependency issues
    with patch('app.core.sentinel.get_logger'):
        # Patch the default add_watch call in __init__ to avoid side effects
        with patch.object(LogSentinel, 'add_watch'):
            return LogSentinel(mock_settings)

def test_add_watch_existing_file(sentinel, tmp_path):
    """Test that add_watch correctly handles existing files"""
    # Create a temporary file with some content
    log_file = tmp_path / "test.log"
    content = "test content"
    log_file.write_text(content)

    sentinel.add_watch(str(log_file))

    resolved_path = str(log_file.resolve())
    assert resolved_path in sentinel.watch_list
    assert sentinel.watch_list[resolved_path] == len(content)

def test_add_watch_new_file(sentinel, tmp_path):
    """Test that add_watch correctly handles and creates new files"""
    # Use a path for a file that doesn't exist yet
    log_file = tmp_path / "new_test.log"

    sentinel.add_watch(str(log_file))

    resolved_path = str(log_file.resolve())
    assert log_file.exists()
    assert resolved_path in sentinel.watch_list
    assert sentinel.watch_list[resolved_path] == 0

def test_init_calls_add_watch_default(mock_settings):
    """Test that LogSentinel initializes with the default log file"""
    with patch('app.core.sentinel.get_logger'):
        with patch.object(LogSentinel, 'add_watch') as mock_add_watch:
            LogSentinel(mock_settings)
            mock_add_watch.assert_called_once_with("logs/kynikos.log")
