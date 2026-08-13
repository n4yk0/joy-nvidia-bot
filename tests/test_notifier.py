from __future__ import annotations

import respx
from httpx import Response

from joy_bot.notifier import TelegramNotifier, format_status
from joy_bot.nvidia import StockItem

ITEM_IN = StockItem(
    sku="LCFEGF50LD90",
    name="NVIDIA RTX 5090",
    is_active=True,
    price="€2,099.00",
    product_url="https://example.com/5090",
)
ITEM_OUT = StockItem(
    sku="NVGFT570",
    name="NVIDIA RTX 5070",
    is_active=False,
    price="€589.00",
    product_url="https://example.com/5070",
)


async def test_sends_in_stock_message(http_client):
    with respx.mock:
        route = respx.post("https://api.telegram.org/botTOKEN/sendMessage").mock(
            return_value=Response(200, json={"ok": True})
        )
        await TelegramNotifier(http_client, "TOKEN", "42").notify_in_stock(ITEM_IN)

    body = route.calls.last.request.content.decode()
    assert '"chat_id":"42"' in body
    assert "RTX 5090" in body
    assert "2,099" in body


async def test_dry_run_skips_http(http_client):
    with respx.mock:
        route = respx.post("https://api.telegram.org/botTOKEN/sendMessage")
        await TelegramNotifier(http_client, "TOKEN", "42", dry_run=True).notify_in_stock(ITEM_IN)

    assert route.call_count == 0


def test_status_format_marks_availability():
    text = format_status([ITEM_IN, ITEM_OUT])
    assert "✅" in text and "❌" in text
    assert "RTX 5090" in text and "RTX 5070" in text


def test_status_format_empty():
    assert "Aucun" in format_status([])
