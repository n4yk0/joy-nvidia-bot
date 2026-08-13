from __future__ import annotations

import respx
from httpx import Response

from joy_bot.commands import TelegramListener
from joy_bot.notifier import TelegramNotifier
from joy_bot.nvidia import NvidiaClient


def _fetcher(payload):
    async def fetch(url, params):
        return payload

    return fetch


def _make(http_client, updates_response, load_fixture):
    nvidia = NvidiaClient(_fetcher(load_fixture("in_stock.json")), "fr-fr")
    notifier = TelegramNotifier(http_client, "TOKEN", "42")
    listener = TelegramListener(http_client, "TOKEN", "42", nvidia, notifier)
    respx.get("https://api.telegram.org/botTOKEN/getUpdates").mock(
        return_value=Response(200, json={"ok": True, "result": updates_response})
    )
    return listener


def _message(text: str, chat_id: str = "42", update_id: int = 1):
    return {
        "update_id": update_id,
        "message": {"chat": {"id": int(chat_id)}, "text": text},
    }


async def test_status_command_replies_with_snapshot(http_client, load_fixture):
    with respx.mock:
        listener = _make(http_client, [_message("/status")], load_fixture)
        send = respx.post("https://api.telegram.org/botTOKEN/sendMessage").mock(
            return_value=Response(200, json={"ok": True})
        )
        updates = await listener._poll()
        for u in updates:
            await listener._handle(u)

    body = send.calls.last.request.content.decode()
    assert "RTX 5090" in body


async def test_test_command_sends_confirmation(http_client, load_fixture):
    with respx.mock:
        listener = _make(http_client, [_message("/test")], load_fixture)
        send = respx.post("https://api.telegram.org/botTOKEN/sendMessage").mock(
            return_value=Response(200, json={"ok": True})
        )
        for u in await listener._poll():
            await listener._handle(u)

    assert "Test" in send.calls.last.request.content.decode()


async def test_unauthorized_chat_is_ignored(http_client, load_fixture):
    with respx.mock:
        listener = _make(http_client, [_message("/status", chat_id="999")], load_fixture)
        send = respx.post("https://api.telegram.org/botTOKEN/sendMessage")
        for u in await listener._poll():
            await listener._handle(u)

    assert send.call_count == 0


async def test_non_command_ignored(http_client, load_fixture):
    with respx.mock:
        listener = _make(http_client, [_message("hello")], load_fixture)
        send = respx.post("https://api.telegram.org/botTOKEN/sendMessage")
        for u in await listener._poll():
            await listener._handle(u)

    assert send.call_count == 0


async def test_unknown_command_shows_help(http_client, load_fixture):
    with respx.mock:
        listener = _make(http_client, [_message("/wat")], load_fixture)
        send = respx.post("https://api.telegram.org/botTOKEN/sendMessage").mock(
            return_value=Response(200, json={"ok": True})
        )
        for u in await listener._poll():
            await listener._handle(u)

    assert "Commandes" in send.calls.last.request.content.decode()


async def test_offset_advances(http_client, load_fixture):
    listener = _make.__wrapped__ if False else None  # noop, silence unused
    nvidia = NvidiaClient(_fetcher(load_fixture("out_of_stock.json")), "fr-fr")
    notifier = TelegramNotifier(http_client, "TOKEN", "42")
    listener = TelegramListener(http_client, "TOKEN", "42", nvidia, notifier)
    with respx.mock:
        respx.get("https://api.telegram.org/botTOKEN/getUpdates").mock(
            return_value=Response(200, json={"ok": True, "result": [_message("/ping", update_id=17)]})
        )
        await listener._poll()

    assert listener._offset == 18
