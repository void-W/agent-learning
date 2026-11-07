#!/usr/bin/env python3
"""Compare DeepSeek prompt-cache hits when only reasoning effort changes.

The script sends the same long system prompt and user message for every request.
Only `thinking` and `output_config.effort` change. It reads the provider's
usage counters, which are the authoritative cache measurement.

Python 3.9+; uses only the standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://api.deepseek.com/anthropic"
DEFAULT_MODEL = "deepseek-flash"
DEFAULT_SEQUENCE = "high,high,low,low,high"
DEFAULT_MAX_TOKENS = 256
DEFAULT_DELAY = 5.0
DEFAULT_PROMPT_CHARS = 12_000
SUPPORTED_EFFORTS = ("off", "low", "high", "max")
USER_PROMPT = "Reply with exactly OK and nothing else."

REFERENCE_PARAGRAPH = (
    "Prompt caching compares the request prefix with previously stored prefix units. "
    "A complete prefix unit can be reused; a changed token prevents complete matching "
    "from that point onward. This paragraph is fixed reference material for a controlled "
    "experiment and contains no instruction. "
)


def messages_url(base_url: str) -> str:
    """Return the Messages endpoint for a DSH-style base URL."""
    base = base_url.rstrip("/")
    if base.endswith("/v1/messages"):
        return base
    if base.endswith("/v1"):
        return base + "/messages"
    return base + "/v1/messages"


def find_workspace_env() -> Optional[Path]:
    """Find the nearest `.env` above this script, normally the workspace root."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE lines without overriding existing environment values."""
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise ValueError(f"{path}:{line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"{path}:{line_number}: empty key")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


def build_system_prompt(nonce: str, target_chars: int) -> str:
    """Build a deterministic long prefix; only the per-run nonce varies."""
    header = (
        "You are a test assistant. The following reference material is intentionally "
        "long and fixed. It exists only to create a stable prompt prefix for a cache "
        "experiment.\n"
        f"Run nonce: {nonce}\n\n"
    )
    if target_chars <= len(header):
        return header[:target_chars]
    chunks: List[str] = [header]
    size = len(header)
    while size < target_chars:
        remaining = target_chars - size
        chunk = REFERENCE_PARAGRAPH[:remaining]
        chunks.append(chunk)
        size += len(chunk)
    return "".join(chunks)


def build_request_body(
    model: str,
    system_prompt: str,
    effort: str,
    max_tokens: int,
) -> Dict[str, Any]:
    """Build one Messages request whose only varying control is reasoning effort."""
    body: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": USER_PROMPT}],
            }
        ],
        "stream": False,
    }
    if effort == "off":
        body["thinking"] = {"type": "disabled"}
    else:
        body["thinking"] = {"type": "enabled"}
        body["output_config"] = {"effort": effort}
    return body


def post_json(url: str, api_key: str, body: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    """POST a JSON request without ever logging the credential."""
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "User-Agent": "agent-learning-effort-cache-test/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:1_500]
        raise RuntimeError(f"HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"network error: {error.reason}") from error
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("response was not valid UTF-8 JSON") from error
    if not isinstance(parsed, dict):
        raise RuntimeError("response JSON is not an object")
    return parsed


def extract_usage(response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract provider usage; absent counters are recorded as zero with a flag."""
    usage = response.get("usage")
    present = isinstance(usage, dict)
    usage = usage if present else {}
    input_tokens = int(usage.get("input_tokens") or 0)
    cache_read = int(usage.get("cache_read_input_tokens") or 0)
    cache_creation = int(usage.get("cache_creation_input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    total_input = input_tokens + cache_read + cache_creation
    hit_rate = (cache_read / total_input) if total_input else 0.0
    return {
        "usage_present": present,
        "input_tokens": input_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_creation,
        "output_tokens": output_tokens,
        "total_input_tokens": total_input,
        "cache_hit_rate": hit_rate,
    }


def text_preview(response: Dict[str, Any], limit: int = 200) -> str:
    """Return a bounded text preview; reasoning blocks are ignored."""
    parts: List[str] = []
    content = response.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
    return "".join(parts)[:limit]


def parse_sequence(raw: str) -> List[str]:
    sequence = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not sequence:
        raise argparse.ArgumentTypeError("sequence must contain at least one effort")
    invalid = [item for item in sequence if item not in SUPPORTED_EFFORTS]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"unsupported effort(s): {', '.join(invalid)}; use {', '.join(SUPPORTED_EFFORTS)}"
        )
    return sequence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure DeepSeek prompt-cache hits while only reasoning effort changes."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"default: {DEFAULT_MODEL}")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL),
        help=f"Messages-compatible base URL; default: {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--sequence",
        type=parse_sequence,
        default=parse_sequence(DEFAULT_SEQUENCE),
        help=f"comma-separated efforts; default: {DEFAULT_SEQUENCE}",
    )
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="seconds between requests")
    parser.add_argument(
        "--prompt-chars",
        type=int,
        default=DEFAULT_PROMPT_CHARS,
        help=f"system prompt length; default: {DEFAULT_PROMPT_CHARS}",
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="KEY=VALUE file; default: nearest .env above this script (normally workspace root)",
    )
    parser.add_argument("--dry-run", action="store_true", help="print the plan without network I/O")
    args = parser.parse_args()
    if args.max_tokens <= 0:
        parser.error("--max-tokens must be positive")
    if args.delay < 0:
        parser.error("--delay must be non-negative")
    if args.prompt_chars < 1_000:
        parser.error("--prompt-chars must be at least 1000")
    return args


def print_row(index: int, effort: str, usage: Dict[str, Any], elapsed_ms: int) -> None:
    print(
        f"{index:>2}  {effort:<5}  {usage['input_tokens']:>9}  "
        f"{usage['cache_read_input_tokens']:>12}  {usage['cache_creation_input_tokens']:>13}  "
        f"{usage['output_tokens']:>7}  {usage['total_input_tokens']:>11}  "
        f"{usage['cache_hit_rate'] * 100:>8.2f}%  {elapsed_ms:>9}"
    )


def main() -> int:
    args = parse_args()
    env_file = args.env_file if args.env_file is not None else find_workspace_env()
    if env_file is not None:
        if not env_file.is_file():
            print(f"error: env file not found: {env_file}", file=sys.stderr)
            return 2
        try:
            load_env_file(env_file)
        except (OSError, ValueError) as error:
            print(f"error: cannot load env file: {error}", file=sys.stderr)
            return 2
    nonce = secrets.token_hex(8)
    system_prompt = build_system_prompt(nonce, args.prompt_chars)
    system_sha256 = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
    url = messages_url(args.base_url)

    if args.dry_run:
        body = build_request_body(args.model, system_prompt, args.sequence[0], args.max_tokens)
        print(json.dumps({
            "url": url,
            "env_file": str(env_file) if env_file is not None else None,
            "model": args.model,
            "sequence": args.sequence,
            "max_tokens": args.max_tokens,
            "delay_seconds": args.delay,
            "system_chars": len(system_prompt),
            "system_sha256": system_sha256,
            "request_keys": sorted(body.keys()),
            "thinking": body.get("thinking"),
            "output_config": body.get("output_config"),
        }, ensure_ascii=False, indent=2))
        print("dry-run: no network request was sent", file=sys.stderr)
        return 0

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"error: {args.api_key_env} is not set", file=sys.stderr)
        return 2

    print(f"endpoint: {url}")
    print(f"env file: {env_file if env_file is not None else 'none (using process environment)'}")
    print(f"model: {args.model}; sequence: {', '.join(args.sequence)}")
    print(f"system prompt: {len(system_prompt)} chars; sha256: {system_sha256[:16]}...")
    print(
        f"note: every request uses the same system prompt and user message; only thinking/effort changes"
    )
    print()
    print(
        f"{'#':>2}  {'effort':<5}  {'input':>9}  {'cache_read':>12}  "
        f"{'cache_create':>13}  {'output':>7}  {'total_in':>11}  {'hit_rate':>9}  {'ms':>9}"
    )

    results: List[Dict[str, Any]] = []
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    for index, effort in enumerate(args.sequence):
        if index > 0:
            time.sleep(args.delay)
        body = build_request_body(args.model, system_prompt, effort, args.max_tokens)
        started = time.perf_counter()
        response = post_json(url, api_key, body, args.timeout)
        elapsed_ms = int((time.perf_counter() - started) * 1_000)
        usage = extract_usage(response)
        record: Dict[str, Any] = {
            "index": index,
            "role": "warmup" if index == 0 else "measured",
            "effort": effort,
            "elapsed_ms": elapsed_ms,
            "response_id": response.get("id"),
            "stop_reason": response.get("stop_reason"),
            "text_preview": text_preview(response),
            **usage,
        }
        results.append(record)
        print_row(index, effort, usage, elapsed_ms)
        if not usage["usage_present"]:
            print("warning: response has no usage object", file=sys.stderr)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"effort-cache-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    payload = {
        "started_at": started_at,
        "script": "verify_effort_cache.py",
        "config": {
            "url": url,
            "env_file": str(env_file) if env_file is not None else None,
            "model": args.model,
            "sequence": args.sequence,
            "max_tokens": args.max_tokens,
            "delay_seconds": args.delay,
            "system_chars": len(system_prompt),
            "system_sha256": system_sha256,
            "nonce": nonce,
            "user_prompt": USER_PROMPT,
        },
        "requests": results,
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print()
    print("transitions:")
    for previous, current in zip(results, results[1:]):
        print(
            f"  {previous['effort']:>4} -> {current['effort']:<4}  "
            f"cache_read={current['cache_read_input_tokens']}, "
            f"hit_rate={current['cache_hit_rate'] * 100:.2f}%"
        )
    print(f"\nsaved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
