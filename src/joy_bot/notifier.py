from __future__ import annotations

import logging
from collections.abc import Iterable
from urllib.parse import urlparse

import httpx

from .nvidia import StockItem

log = logging.getLogger(__name__)

_ALLOWED_LINK_HOSTS = frozenset({"marketplace.nvidia.com", "www.nvidia.com", "nvidia.com"})


def _safe_product_link(url: str | None) -> str | None:
    if not url:
        return None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_LINK_HOSTS:
        return None
    return url


class TelegramNotifier:
    def __init__(
        self,
        client: httpx.AsyncClient,
        token: str,
        chat_id: str,
        dry_run: bool = False,
    ) -> None:
        self._client = client
        self._url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._chat_id = chat_id
        self._dry_run = dry_run

    async def send_text(self, text: str) -> None:
        if self._dry_run:
            log.info("[dry-run] would send: %s", text.replace("\n", " | "))
            return
        response = await self._client.post(
            self._url,
            json={
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            },
        )
        response.raise_for_status()

    async def notify_in_stock(self, item: StockItem) -> None:
        await self.send_text(format_in_stock(item))

    async def notify_status(self, items: Iterable[StockItem]) -> None:
        await self.send_text(format_status(items))


def format_in_stock(item: StockItem) -> str:
    price = f"\n*Prix:* {item.price}" if item.price else ""
    safe_url = _safe_product_link(item.product_url)
    link = f"\n[Acheter maintenant]({safe_url})" if safe_url else ""
    return f"\U0001f6a8 *{item.name}* est en stock !{price}{link}"


def format_status(items: Iterable[StockItem]) -> str:
    items = list(items)
    if not items:
        return "ℹ️ Aucun produit renvoyé par Nvidia."

    founders = [i for i in items if i.is_founders]
    partners = [i for i in items if not i.is_founders]

    def _line(i: StockItem) -> str:
        icon = "✅" if i.is_active else "❌"
        price = f" — {i.price}" if i.price else ""
        link_url = _safe_product_link(i.product_url)
        link = f" · [voir]({link_url})" if link_url else ""
        return f"{icon} *{i.name}*{price}{link}"

    lines = ["*État du stock Nvidia FE*"]
    lines += [_line(i) for i in founders] if founders else ["_aucune FE listée_"]

    if partners:
        p_in = sum(1 for i in partners if i.is_active)
        lines += ["", f"_Canary — cartes partenaires ({p_in}/{len(partners)} en stock)_"]
        lines += [_line(i) for i in partners]

    return "\n".join(lines)
