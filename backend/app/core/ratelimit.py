"""A small in-memory limiter for failed login attempts.

Without it, anybody can try passwords at the speed of the server. Failures are
counted per key (the caller uses client address + username); once a key has
`max_failures` failures within `window` seconds it is locked until the oldest
of them leaves the window. A successful login clears the key.

It lives in the memory of one process: with several workers each one counts on
its own, so the real limit is `max_failures` times the number of workers. That
is still enough to make guessing a password impractical, without adding a
database table or a dependency.

Behind a reverse proxy, the client address is the proxy's unless uvicorn is
started with --proxy-headers and --forwarded-allow-ips; in that case every
user shares the same counters per username.
"""

import time
from collections import defaultdict, deque
from typing import Callable


class LoginLimiter:
    def __init__(
        self,
        max_failures: int = 10,
        window: float = 300.0,
        max_keys: int = 10_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_failures = max_failures
        self.window = window
        self.max_keys = max_keys
        self._clock = clock
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> deque[float]:
        events = self._failures[key]
        while events and now - events[0] >= self.window:
            events.popleft()
        if not events:
            self._failures.pop(key, None)
        return events

    def retry_after(self, key: str) -> int:
        """Seconds to wait before `key` may try again (0 if it may now)."""
        if key not in self._failures:
            return 0
        now = self._clock()
        events = self._prune(key, now)
        if len(events) < self.max_failures:
            return 0
        return max(1, int(events[0] + self.window - now) + 1)

    def record_failure(self, key: str) -> None:
        now = self._clock()
        if key not in self._failures and len(self._failures) >= self.max_keys:
            self._drop_expired(now)
            if len(self._failures) >= self.max_keys:
                # Still full of live keys (someone is spraying random names):
                # forget the oldest one rather than grow without bound.
                self._failures.pop(next(iter(self._failures)))
        self._failures[key].append(now)

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)

    def clear(self) -> None:
        self._failures.clear()

    def _drop_expired(self, now: float) -> None:
        for key in list(self._failures):
            self._prune(key, now)
