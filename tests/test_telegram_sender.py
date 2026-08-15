from unittest.mock import MagicMock, patch

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


def test_empty_text_is_a_noop_returning_true():
    with patch("notification_sender.telegram_sender.httpx.post") as post:
        assert send_markdown("   ", "TOKEN", "CHAT") is True
    assert post.call_count == 0
