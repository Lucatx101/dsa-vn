"""Telegram Bot API sender. Failures are logged, never raised — a broken
notification must not abort the rest of the watchlist run."""

import logging

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_LIMIT = 4096
TIMEOUT_SECONDS = 30.0


def _chunks(text: str, size: int = TELEGRAM_LIMIT) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def send_markdown(text: str, bot_token: str, chat_id: str) -> bool:
    """Send Markdown text to a Telegram chat. Returns success as a bool.

    Never raises: every failure path (string handling before the network
    call, the request itself, a non-2xx response) is caught here and turned
    into a ``False`` return so a broken notification never aborts the
    caller's run.
    """
    try:
        if not text.strip():
            return True

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        for chunk in _chunks(text):
            response = httpx.post(
                url,
                json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"},
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - notification failure is non-fatal
        logger.error("Telegram send failed: %s", exc)
        return False

    return True
