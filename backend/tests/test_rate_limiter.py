
from config.rate_limiter import InMemoryRateLimiter


def test_allows_requests_within_limit():
    limiter = InMemoryRateLimiter(limit=3, window_seconds=60)

    assert limiter.check("client-a", now=100) is None
    assert limiter.check("client-a", now=101) is None
    assert limiter.check("client-a", now=102) is None


def test_rejects_request_after_limit():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)

    assert limiter.check("client-a", now=100) is None
    assert limiter.check("client-a", now=101) is None

    retry_after = limiter.check("client-a", now=102)

    assert retry_after == 58


def test_allows_request_after_window_expires():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)

    assert limiter.check("client-a", now=100) is None
    assert limiter.check("client-a", now=101) is None
    assert limiter.check("client-a", now=160) is None


def test_clients_have_independent_limits():
    limiter = InMemoryRateLimiter(limit=1, window_seconds=60)

    assert limiter.check("client-a", now=100) is None
    assert limiter.check("client-a", now=101) == 59
    assert limiter.check("client-b", now=101) is None


def test_limiter_bounds_number_of_clients():
    limiter = InMemoryRateLimiter(
        limit=5,
        window_seconds=60,
        max_clients=2,
    )

    assert limiter.check("client-a", now=100) is None
    assert limiter.check("client-b", now=100) is None
    assert limiter.check("client-c", now=100) is None

    assert len(limiter.requests) == 2
    assert "client-a" not in limiter.requests
    assert "client-c" in limiter.requests

