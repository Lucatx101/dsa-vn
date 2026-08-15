from unittest.mock import MagicMock, patch

import httpx

from notification_sender.telegram_sender import TELEGRAM_LIMIT, send_markdown


def _ok_response():
    response = MagicMock()
    response.raise_for_status.return_value = None
    return response


def test_sends_single_message_and_returns_true():
    with patch("notification_sender.telegram_sender.httpx.post") as post:
        post.return_value = _ok_response()
        assert send_markdown("xin chào", "TOKEN", "CHAT") is True

    assert post.call_count == 1
    payload = post.call_args.kwargs["json"]
    assert payload["chat_id"] == "CHAT"
    assert payload["text"] == "xin chào"
    assert "TOKEN" in post.call_args.args[0]


def test_payload_never_includes_parse_mode():
    """Regression guard for a live-API finding: chunking is purely
    character-count based, so a **bold**/_italic_ entity's opening marker
    can land in one chunk while its closing marker lands in the next.
    Telegram's legacy Markdown parser then rejects the *entire* chunk
    containing the orphaned opening marker with HTTP 400 ("can't find end
    of the entity..."), confirmed against the live API on a real,
    formatting-dense dashboard. Sending plain text (no parse_mode) avoids
    this failure mode; this test ensures parse_mode doesn't silently creep
    back into the payload.
    """
    with patch("notification_sender.telegram_sender.httpx.post") as post:
        post.return_value = _ok_response()
        assert send_markdown("**bold** and _italic_ text", "TOKEN", "CHAT") is True

    assert post.call_count == 1
    payload = post.call_args.kwargs["json"]
    assert "parse_mode" not in payload
    assert payload == {"chat_id": "CHAT", "text": "**bold** and _italic_ text"}


def test_splits_long_message_into_multiple_requests():
    long_text = "a" * (TELEGRAM_LIMIT * 2 + 10)
    with patch("notification_sender.telegram_sender.httpx.post") as post:
        post.return_value = _ok_response()
        assert send_markdown(long_text, "TOKEN", "CHAT") is True

    assert post.call_count == 3
    for call in post.call_args_list:
        assert len(call.kwargs["json"]["text"]) <= TELEGRAM_LIMIT


def test_returns_false_on_http_error_without_raising():
    with patch("notification_sender.telegram_sender.httpx.post") as post:
        post.side_effect = RuntimeError("connection refused")
        assert send_markdown("xin chào", "TOKEN", "CHAT") is False


def test_returns_false_on_non_2xx_response_without_raising():
    """Distinct failure mode from the network-level test above: httpx.post()
    itself succeeds, but the response is a genuine Telegram API rejection
    (e.g. bad bot token -> 401), which raise_for_status() turns into an
    HTTPStatusError. This proves raise_for_status() is actually called and
    that its exception is caught rather than a future refactor silently
    dropping or misplacing that call.
    """
    request = httpx.Request("POST", "https://api.telegram.org/botTOKEN/sendMessage")
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized",
        request=request,
        response=httpx.Response(401, request=request),
    )
    with patch("notification_sender.telegram_sender.httpx.post") as post:
        post.return_value = response
        assert send_markdown("xin chào", "TOKEN", "CHAT") is False

    assert post.call_count == 1


def test_empty_text_is_a_noop_returning_true():
    with patch("notification_sender.telegram_sender.httpx.post") as post:
        assert send_markdown("   ", "TOKEN", "CHAT") is True
    assert post.call_count == 0
