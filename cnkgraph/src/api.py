"""
Async HTTP client for cnkgraph API with rate limiting and retry.
"""

import asyncio
import json
import random
from typing import Any

import aiohttp

BASE_URL = "https://api.cnkgraph.com/api"

DEFAULT_TIMEOUT = 30
DEFAULT_CONCURRENCY = 2
DEFAULT_DELAY = 0.5
MAX_RETRIES = 3
CONSECUTIVE_FAIL_LIMIT = 5


class CnkgraphClient:
    """Async HTTP client with semaphore-based concurrency control."""

    def __init__(self, concurrency: int = DEFAULT_CONCURRENCY, delay: float = DEFAULT_DELAY):
        self.semaphore = asyncio.Semaphore(concurrency)
        self.delay = delay
        self._session: aiohttp.ClientSession | None = None
        self._consecutive_fails = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get(self, path: str, params: dict | None = None, *, timeout: int | None = None) -> dict | list | None:
        """GET request with retry, rate limiting, and error handling."""
        url = f"{BASE_URL}{path}"
        async with self.semaphore:
            await asyncio.sleep(self.delay + random.uniform(0, 0.1))
            return await self._request_with_retry(url, params, timeout)

    async def _request_with_retry(self, url: str, params: dict | None = None, timeout: int | None = None) -> dict | list | None:
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                timeout_val = aiohttp.ClientTimeout(total=timeout or DEFAULT_TIMEOUT)
                session = await self._get_session()
                async with session.get(url, params=params, timeout=timeout_val) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get("Content-Type", "")
                        if "json" not in content_type:
                            print(f"  [WARN] Non-JSON response for {url}: {content_type}")
                            self._consecutive_fails += 1
                            return None

                        data = await resp.json()
                        self._consecutive_fails = 0
                        return data

                    elif resp.status == 429:
                        # Rate limited — back off significantly
                        wait = 30 * (attempt + 1)
                        print(f"  [RATE LIMIT] 429 on {url}, waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(wait)
                        continue

                    elif resp.status >= 500:
                        wait = 2 ** attempt
                        print(f"  [RETRY] {resp.status} on {url}, wait {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(wait)
                        continue

                    else:
                        text = await resp.text()
                        print(f"  [ERROR] {resp.status} on {url}: {text[:200]}")
                        return None

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                wait = 2 ** attempt
                print(f"  [RETRY] {type(e).__name__} on {url}, wait {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(wait)
                continue

        print(f"  [FAIL] All retries exhausted for {url}: {last_error}")
        self._consecutive_fails += 1
        return None

    @property
    def should_abort(self) -> bool:
        """Check if too many consecutive failures suggest we should stop."""
        return self._consecutive_fails >= CONSECUTIVE_FAIL_LIMIT

    def reset_fail_counter(self):
        self._consecutive_fails = 0


async def fetch_json(url: str) -> dict | list | None:
    """Simple one-off fetch for CLI status checks."""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
    return None
