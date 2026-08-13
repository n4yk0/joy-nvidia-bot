from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from curl_cffi.requests import AsyncSession
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

SEARCH_URL = "https://api.nvidia.partners/edge/product/search"

IN_STOCK_STATUSES = {"in_stock", "buy_now"}

Fetcher = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True, slots=True)
class StockItem:
    sku: str
    name: str
    is_active: bool
    price: str | None
    product_url: str | None


class NvidiaClient:
    def __init__(self, fetch: Fetcher, locale: str) -> None:
        self._fetch = fetch
        self._locale = locale

    async def fetch_inventory(self) -> list[StockItem]:
        payload = await self._fetch(
            SEARCH_URL,
            {
                "page": 1,
                "limit": 100,
                "locale": self._locale,
                "category": "GPU",
                "manufacturer": "NVIDIA",
            },
        )
        return self._parse(payload)

    @staticmethod
    def _parse(payload: dict[str, Any]) -> list[StockItem]:
        products = (payload.get("searchedProducts") or {}).get("productDetails") or []
        items: list[StockItem] = []
        for p in products:
            sku = p.get("productSKU") or ""
            if not sku:
                continue
            status = (p.get("prdStatus") or "").lower()
            items.append(
                StockItem(
                    sku=sku,
                    name=p.get("displayName") or sku,
                    is_active=status in IN_STOCK_STATUSES,
                    price=p.get("productPrice"),
                    product_url=p.get("internalLink"),
                )
            )
        return items


class CurlCffiFetcher:
    def __init__(self, session: AsyncSession, locale: str) -> None:
        self._session = session
        self._headers = {
            "Accept": "application/json",
            "Accept-Language": locale,
            "Origin": "https://marketplace.nvidia.com",
            "Referer": "https://marketplace.nvidia.com/",
        }

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def __call__(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        response = await self._session.get(url, params=params, headers=self._headers, timeout=15)
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code} from {url}")
        return response.json()
