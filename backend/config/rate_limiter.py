
from collections import OrderedDict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request


RATE_LIMIT = 30
WINDOW_SECONDS = 60
MAX_CLIENTS = 10_000


class InMemoryRateLimiter:
    def __init__(
        self,
        limit=RATE_LIMIT,
        window_seconds=WINDOW_SECONDS,
        max_clients=MAX_CLIENTS,
    ):
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self.requests = OrderedDict()
        self.lock = Lock()

    def check(self, client_id, now=None):
        if now is None:
            now = monotonic()

        with self.lock:
            timestamps = self.requests.get(client_id)

            if timestamps is None:
                timestamps = deque()
                self.requests[client_id] = timestamps
            else:
                self.requests.move_to_end(client_id)

            while (
                timestamps
                and now - timestamps[0] >= self.window_seconds
            ):
                timestamps.popleft()

            if len(timestamps) >= self.limit:
                retry_after = max(
                    1,
                    int(
                        self.window_seconds
                        - (now - timestamps[0])
                    ),
                )
                return retry_after

            timestamps.append(now)
            self.requests.move_to_end(client_id)

            # Bound memory usage by evicting least-recently-used clients.
            while len(self.requests) > self.max_clients:
                self.requests.popitem(last=False)

            return None


rate_limiter = InMemoryRateLimiter()


def enforce_rate_limit(request: Request):
    client = request.client
    client_id = client.host if client else "unknown"

    retry_after = rate_limiter.check(client_id)

    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
