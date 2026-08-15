from __future__ import annotations

import pytest

from joy_bot.nvidia import NvidiaClient


def _fetcher(payload: dict):
    async def fetch(url, params):
        return payload

    return fetch


async def test_parses_in_stock_and_flags_founders(load_fixture):
    payload = load_fixture("in_stock.json")
    items = await NvidiaClient(_fetcher(payload), "fr-fr").fetch_inventory()

    by_sku = {i.sku: i for i in items}
    assert by_sku["LCFEGF50LD90"].is_active is True
    assert by_sku["LCFEGF50LD90"].is_founders is True
    assert by_sku["ASUS3050"].is_active is True
    assert by_sku["ASUS3050"].is_founders is False


async def test_all_out_of_stock(load_fixture):
    payload = load_fixture("out_of_stock.json")
    items = await NvidiaClient(_fetcher(payload), "fr-fr").fetch_inventory()

    assert items
    assert all(not i.is_active for i in items)


async def test_empty_payload_yields_no_items():
    payload = {"searchedProducts": {"productDetails": []}}
    items = await NvidiaClient(_fetcher(payload), "fr-fr").fetch_inventory()
    assert items == []


async def test_fetcher_error_propagates():
    async def broken(url, params):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await NvidiaClient(broken, "fr-fr").fetch_inventory()
