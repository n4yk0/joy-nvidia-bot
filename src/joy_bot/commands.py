from __future__ import annotations

import asyncio
import logging

import httpx

from .notifier import TelegramNotifier, format_status
from .nvidia import NvidiaClient

log = logging.getLogger(__name__)

LONG_POLL_TIMEOUT = 25


class TelegramListener:
    def __init__(
        self,
        client: httpx.AsyncClient,
        token: str,
        allowed_chat_id: str,
        nvidia: NvidiaClient,
        notifier: TelegramNotifier,
    ) -> None:
        self._client = client
        self._url = f"https://api.telegram.org/bot{token}/getUpdates"
        self._allowed_chat_id = str(allowed_chat_id)
        self._nvidia = nvidia
        self._notifier = notifier
        self._offset: int | None = None

    async def run(self, stop: asyncio.Event) -> None:
        log.info("telegram command listener started")
        while not stop.is_set():
            try:
                updates = await self._poll()
            except (httpx.HTTPError, ValueError) as exc:
                log.warning("getUpdates failed: %s", exc)
                await asyncio.sleep(5)
                continue
            for update in updates:
                await self._handle(update)

    async def _poll(self) -> list[dict]:
        params: dict[str, int] = {"timeout": LONG_POLL_TIMEOUT}
        if self._offset is not None:
            params["offset"] = self._offset
        response = await self._client.get(
            self._url, params=params, timeout=LONG_POLL_TIMEOUT + 10
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise ValueError(f"getUpdates not ok: {payload}")
        updates = payload.get("result", [])
        if updates:
            self._offset = updates[-1]["update_id"] + 1
        return updates

    async def _handle(self, update: dict) -> None:
        message = update.get("message") or update.get("edited_message") or {}
        chat_id = str((message.get("chat") or {}).get("id", ""))
        text = (message.get("text") or "").strip()
        if not text.startswith("/"):
            return
        if chat_id != self._allowed_chat_id:
            log.info("ignored command from unauthorized chat %s", chat_id)
            return
        cmd = text.split()[0].split("@")[0].lower()
        await self._dispatch(cmd)

    async def _dispatch(self, cmd: str) -> None:
        if cmd == "/ping":
            await self._notifier.send_text("pong")
        elif cmd == "/test":
            await self._notifier.send_text("✅ Test — le bot est actif.")
        elif cmd in ("/status", "/start"):
            try:
                items = await self._nvidia.fetch_inventory()
            except Exception:  # noqa: BLE001
                log.exception("nvidia fetch failed in /status handler")
                await self._notifier.send_text(
                    "⚠️ Impossible de récupérer le stock Nvidia — réessayez dans quelques instants."
                )
                return
            await self._notifier.send_text(format_status(items))
        else:
            await self._notifier.send_text(
                "Commandes: /status /test /ping"
            )
