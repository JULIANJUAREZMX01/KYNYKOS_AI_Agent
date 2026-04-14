import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Try to import pytest, but don't fail if it's missing (for the manual runner)
try:
    import pytest
except ImportError:
    pytest = None

# Define mocks for external dependencies
mock_tenacity = MagicMock()
mock_tenacity.retry = lambda *args, **kwargs: (lambda f: f)
mock_tenacity.stop_after_attempt = MagicMock()
mock_tenacity.wait_exponential = MagicMock()

mock_groq = MagicMock()
mock_anthropic = MagicMock()
mock_yaml = MagicMock()
mock_loguru = MagicMock()

# Define mocks for internal dependencies
mock_settings = MagicMock()
mock_settings.groq_api_key = "test_groq_key"
mock_settings.anthropic_api_key = "test_anthropic_key"

mock_config = MagicMock()
mock_config.Settings = MagicMock(return_value=mock_settings)

mock_utils = MagicMock()
mock_logger = MagicMock()
mock_utils.get_logger = MagicMock(return_value=mock_logger)

# Dependency dictionary for patch.dict
MOCK_DEPENDENCIES = {
    'tenacity': mock_tenacity,
    'groq': mock_groq,
    'anthropic': mock_anthropic,
    'yaml': mock_yaml,
    'loguru': mock_loguru,
    'app.config': mock_config,
    'app.utils': mock_utils,
}

if pytest:
    @pytest.fixture(autouse=True)
    def mock_dependencies():
        """Mock missing dependencies safely using patch.dict on sys.modules"""
        with patch.dict(sys.modules, MOCK_DEPENDENCIES):
            # Import within the patch context
            from app.cloud.providers import ProviderManager
            yield ProviderManager

async def test_fallback_logic_success(ProviderManager):
    """Case 1: Groq succeeds (Happy Path)"""
    manager = ProviderManager(mock_settings)

    # Setup mocks for providers
    manager.groq_provider = MagicMock()
    manager.groq_provider.name = "groq"
    manager.groq_provider.call = AsyncMock()

    manager.anthropic_provider = MagicMock()
    manager.anthropic_provider.name = "anthropic"
    manager.anthropic_provider.call = AsyncMock()

    messages = [{"role": "user", "content": "hello"}]

    manager.groq_provider.call.return_value = {"text": "Groq response"}
    response = await manager.call(messages)

    assert response["text"] == "Groq response"
    manager.anthropic_provider.call.assert_not_called()


async def test_fallback_logic_fallback_success(ProviderManager):
    """Case 2: Groq fails, Anthropic succeeds (Fallback Path)"""
    manager = ProviderManager(mock_settings)

    # Setup mocks for providers
    manager.groq_provider = MagicMock()
    manager.groq_provider.name = "groq"
    manager.groq_provider.call = AsyncMock()

    manager.anthropic_provider = MagicMock()
    manager.anthropic_provider.name = "anthropic"
    manager.anthropic_provider.call = AsyncMock()

    messages = [{"role": "user", "content": "hello"}]

    manager.groq_provider.call.side_effect = Exception("Groq error")
    manager.anthropic_provider.call.return_value = {"text": "Anthropic fallback response"}

    response = await manager.call(messages)

    assert response["text"] == "Anthropic fallback response"
    manager.anthropic_provider.call.assert_called_once()


async def test_fallback_logic_both_fail(ProviderManager):
    """Case 3: Both Groq and Anthropic fail (Double Failure Path)"""
    manager = ProviderManager(mock_settings)

    # Setup mocks for providers
    manager.groq_provider = MagicMock()
    manager.groq_provider.name = "groq"
    manager.groq_provider.call = AsyncMock()

    manager.anthropic_provider = MagicMock()
    manager.anthropic_provider.name = "anthropic"
    manager.anthropic_provider.call = AsyncMock()

    messages = [{"role": "user", "content": "hello"}]

    manager.groq_provider.call.side_effect = Exception("Groq error")
    manager.anthropic_provider.call.side_effect = Exception("Anthropic error")

    try:
        await manager.call(messages)
        raise AssertionError("Expected Exception was not raised")
    except Exception as e:
        assert str(e) == "Anthropic error"


async def test_fallback_logic_no_fallback_configured(ProviderManager):
    """Case 4: Groq fails, no Anthropic provider configured (No Fallback Path)"""
    manager = ProviderManager(mock_settings)

    # Setup mocks for providers
    manager.groq_provider = MagicMock()
    manager.groq_provider.name = "groq"
    manager.groq_provider.call = AsyncMock()

    manager.anthropic_provider = None

    messages = [{"role": "user", "content": "hello"}]

    manager.groq_provider.call.side_effect = Exception("Groq error")

    try:
        await manager.call(messages)
        raise AssertionError("Expected Exception was not raised")
    except Exception as e:
        assert str(e) == "Groq error"

if __name__ == "__main__":
    # Standard manual runner for environments where pytest is missing
    async def run_tests():
        # Setup the mocks manually for the standalone run
        with patch.dict(sys.modules, MOCK_DEPENDENCIES):
            from app.cloud.providers import ProviderManager

            try:
                await test_fallback_logic_success(ProviderManager)
                print("test_fallback_logic_success: PASSED")
                await test_fallback_logic_fallback_success(ProviderManager)
                print("test_fallback_logic_fallback_success: PASSED")
                await test_fallback_logic_both_fail(ProviderManager)
                print("test_fallback_logic_both_fail: PASSED")
                await test_fallback_logic_no_fallback_configured(ProviderManager)
                print("test_fallback_logic_no_fallback_configured: PASSED")
                print("\nAll tests passed successfully!")
            except Exception as e:
                print(f"Test FAILED: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

    asyncio.run(run_tests())
