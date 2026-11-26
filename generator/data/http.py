"""Tiny stdlib HTTP helpers with retries (no requests dependency)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

USER_AGENT = "profile-readme-generator"


def get(url: str, token: str | None = None, accept: str = "application/json", retries: int = 3) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return _send(urllib.request.Request(url, headers=headers), retries)


def get_json(url: str, token: str | None = None, retries: int = 3):
    return json.loads(get(url, token, "application/vnd.github+json", retries))


def post_json(url: str, payload: dict, token: str, retries: int = 3):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "User-Agent": USER_AGENT,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    return json.loads(_send(request, retries))


def _send(request: urllib.request.Request, retries: int) -> bytes:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            # 4xx other than rate limiting will not get better by retrying.
            if error.code < 500 and error.code not in (403, 429) or attempt == retries - 1:
                raise
        except urllib.error.URLError:
            if attempt == retries - 1:
                raise
        time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")
