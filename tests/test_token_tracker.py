import pytest
from app.services.token_tracker import TokenTracker


def test_track_token_usage():
    """Should track tokens used per provider"""
    tracker = TokenTracker()
    tracker.add_usage("anthropic", tokens_used=1000)
    remaining = tracker.get_remaining("anthropic")
    assert remaining < tracker.limit_per_minute["anthropic"]


def test_rate_limit_detection_boundaries():
    """Should detect when provider hits rate limit threshold (90%)"""
    tracker = TokenTracker()
    limit = tracker.limit_per_minute["groq"] # 30000

    # 89.9% of limit: 30000 * 0.899 = 26970
    tracker.reset_minute("groq")
    tracker.add_usage("groq", tokens_used=int(limit * 0.899))
    assert tracker.is_rate_limited("groq") == False

    # 90% of limit: 30000 * 0.9 = 27000
    tracker.reset_minute("groq")
    tracker.add_usage("groq", tokens_used=int(limit * 0.9))
    assert tracker.is_rate_limited("groq") == True

    # 90.1% of limit: 30000 * 0.901 = 27030
    tracker.reset_minute("groq")
    tracker.add_usage("groq", tokens_used=int(limit * 0.901))
    assert tracker.is_rate_limited("groq") == True


def test_rate_limit_unknown_provider():
    """Should return False for unknown providers"""
    tracker = TokenTracker()
    assert tracker.is_rate_limited("unknown_provider") == False


def test_rate_limit_infinite():
    """Should return False for providers with infinite limit"""
    tracker = TokenTracker()
    tracker.add_usage("ollama", tokens_used=999999999)
    assert tracker.is_rate_limited("ollama") == False


def test_reset_minute():
    """Should reset usage counters for a provider"""
    tracker = TokenTracker()
    tracker.add_usage("openai", tokens_used=5000, requests=5)

    assert tracker.usage["openai"]["tokens_used"] == 5000
    assert tracker.usage["openai"]["requests_made"] == 5

    tracker.reset_minute("openai")

    assert tracker.usage["openai"]["tokens_used"] == 0
    assert tracker.usage["openai"]["requests_made"] == 0


def test_get_remaining_infinite():
    """Should return a large number for infinite limits"""
    tracker = TokenTracker()
    assert tracker.get_remaining("ollama") == 1000000000


def test_get_remaining_standard():
    """Should return correct remaining tokens"""
    tracker = TokenTracker()
    limit = tracker.limit_per_minute["anthropic"]
    tracker.add_usage("anthropic", tokens_used=10000)
    assert tracker.get_remaining("anthropic") == limit - 10000
