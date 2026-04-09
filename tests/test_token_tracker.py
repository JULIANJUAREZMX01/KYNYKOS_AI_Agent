import pytest
from app.services.token_tracker import TokenTracker


def test_track_token_usage():
    """Should track tokens used per provider"""
    tracker = TokenTracker()
    tracker.add_usage("anthropic", tokens_used=1000)
    remaining = tracker.get_remaining("anthropic")
    assert remaining < tracker.limit_per_minute["anthropic"]


def test_rate_limit_detection():
    """Should detect when provider hits rate limit"""
    tracker = TokenTracker()
    tracker.add_usage("groq", tokens_used=27000)  # Close to 30k limit
    is_limited = tracker.is_rate_limited("groq")
    assert is_limited == True


def test_reset_minute():
    """Should reset counters for a specific provider"""
    tracker = TokenTracker()

    # Setup usage for two providers
    tracker.add_usage("anthropic", tokens_used=1000, requests=2)
    tracker.add_usage("groq", tokens_used=500, requests=1)

    # Verify initial state
    assert tracker.usage["anthropic"]["tokens_used"] == 1000
    assert tracker.usage["anthropic"]["requests_made"] == 2
    assert tracker.usage["groq"]["tokens_used"] == 500
    assert tracker.usage["groq"]["requests_made"] == 1

    # Reset one provider
    tracker.reset_minute("anthropic")

    # Verify reset provider
    assert tracker.usage["anthropic"]["tokens_used"] == 0
    assert tracker.usage["anthropic"]["requests_made"] == 0

    # Verify other provider remains unaffected
    assert tracker.usage["groq"]["tokens_used"] == 500
    assert tracker.usage["groq"]["requests_made"] == 1
