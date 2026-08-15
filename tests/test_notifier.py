from __future__ import annotations

import respx
from httpx import Response

from joy_bot.notifier import TelegramNotifier, format_status
from joy_bot.nvidia import StockItem

FE_IN = StockItem(
    sku="LCFEGF50LD90",
    name="NVIDIA RTX 5090",
    is_active=True,
    is_founders=True,
    price="€2,099.00",
    product_url="https://example.com/5090",
)
FE_OUT = StockItem(
    sku="NVGFT570",
    name="NVIDIA RTX 5070",
    is_active=False,
    is_founders=True,
    price="€589.00",
    product_url="https://example.com/5070",
)
PARTNER_IN = StockItem(
    sku="ASUS3050",
    name="ASUS RTX 3050",
    is_active=True,
    is_founders=False,
    price="€252.99",
    product_url="https://example.com/asus-3050",
)


async def test_sends_in_stock_message(http_client):
    with respx.mock:
        route = respx.post("https://api.telegram.org/botTOKEN/sendMessage").mock(
            return_value=Response(200, json={"ok": True})
        )
        await TelegramNotifier(http_client, "TOKEN", "42").notify_in_stock(FE_IN)

    body = route.calls.last.request.content.decode()
    assert '"chat_id":"42"' in body
    assert "RTX 5090" in body
    assert "2,099" in body


async def test_dry_run_skips_http(http_client):
    with respx.mock:
        route = respx.post("https://api.telegram.org/botTOKEN/sendMessage")
        await TelegramNotifier(http_client, "TOKEN", "42", dry_run=True).notify_in_stock(FE_IN)

    assert route.call_count == 0


def test_status_shows_fe_and_partners_separately():
    text = format_status([FE_IN, FE_OUT, PARTNER_IN])
    assert "Nvidia FE" in text
    assert "Canary" in text and "1/1 en stock" in text
    assert "NVIDIA RTX 5090" in text and "ASUS RTX 3050" in text


def test_status_without_partners_omits_canary():
    text = format_status([FE_IN, FE_OUT])
    assert "Canary" not in text


def test_status_without_fe_shows_placeholder():
    text = format_status([PARTNER_IN])
    assert "aucune FE" in text
    assert "Canary" in text


def test_status_format_empty():
    assert "Aucun" in format_status([])
