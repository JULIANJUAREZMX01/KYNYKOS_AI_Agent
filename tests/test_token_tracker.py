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
