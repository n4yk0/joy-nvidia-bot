from __future__ import annotations

import argparse
import asyncio
import logging
import random
import signal
from contextlib import asynccontextmanager, suppress

import httpx
from curl_cffi.requests import AsyncSession

from .commands import TelegramListener
from .config import Settings
from .notifier import TelegramNotifier
from .nvidia import CurlCffiFetcher, NvidiaClient
from .state import StateTracker

log = logging.getLogger("joy_bot")


@asynccontextmanager
async def _components(settings: Settings):
    async with (
        AsyncSession(impersonate=settings.impersonate) as nv_session,
        httpx.AsyncClient(timeout=10.0) as tg_client,
    ):
        nvidia = NvidiaClient(CurlCffiFetcher(nv_session, settings.locale), settings.locale)
        notifier = TelegramNotifier(
            tg_client, settings.telegram_token, settings.telegram_chat_id, settings.dry_run
        )
        yield tg_client, nvidia, notifier


async def run_watch(settings: Settings) -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop.set)

    async with _components(settings) as (tg_client, nvidia, notifier):
        state = StateTracker(settings.state_file)
        listener = TelegramListener(
            tg_client, settings.telegram_token, settings.telegram_chat_id, nvidia, notifier
        )

        log.info(
            "watching Nvidia %s marketplace, interval=%.0fs",
            settings.locale,
            settings.poll_interval,
        )
        listener_task = asyncio.create_task(listener.run(stop), name="tg-listener")
        try:
            await _stock_loop(settings, nvidia, notifier, state, stop)
        finally:
            listener_task.cancel()
            with suppress(asyncio.CancelledError):
                await listener_task
        log.info("shutting down")


async def _stock_loop(
    settings: Settings,
    nvidia: NvidiaClient,
    notifier: TelegramNotifier,
    state: StateTracker,
    stop: asyncio.Event,
) -> None:
    while not stop.is_set():
        await _tick(nvidia, notifier, state)
        delay = settings.poll_interval + random.uniform(0, settings.poll_jitter)
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=delay)


async def _tick(
    nvidia: NvidiaClient, notifier: TelegramNotifier, state: StateTracker
) -> None:
    try:
        items = await nvidia.fetch_inventory()
    except Exception as exc:  # noqa: BLE001 — curl_cffi surfaces varied error types
        log.warning("fetch failed: %r", exc)
        return

    if not items:
        log.warning("empty product list — API shape may have changed")
        return

    founders = [i for i in items if i.is_founders]
    log.debug(
        "polled %d items (%d FE): %s",
        len(items),
        len(founders),
        ", ".join(f"{i.name.split()[-1]}={'IN' if i.is_active else 'out'}" for i in founders),
    )

    for item in founders:
        if state.transitioned_to_in_stock(item.sku, item.is_active):
            log.info("IN STOCK: %s (%s)", item.name, item.sku)
            try:
                await notifier.notify_in_stock(item)
            except httpx.HTTPError as exc:
                log.error("telegram send failed for %s: %s", item.sku, exc)
                continue
        state.update(item.sku, item.is_active)
    state.flush()


async def run_test(settings: Settings) -> None:
    async with _components(settings) as (_, _nvidia, notifier):
        await notifier.send_text("✅ Test — le bot peut vous joindre.")
        log.info("test message sent")


async def run_status(settings: Settings) -> None:
    async with _components(settings) as (_, nvidia, notifier):
        items = await nvidia.fetch_inventory()
        await notifier.notify_status(items)
        log.info("status sent (%d items)", len(items))


def cli() -> None:
    parser = argparse.ArgumentParser(prog="joy-bot")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("watch", help="run the stock watch loop (default)")
    sub.add_parser("test", help="send a test Telegram message and exit")
    sub.add_parser("status", help="fetch once and push a stock snapshot to Telegram")
    args = parser.parse_args()

    settings = Settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    action = {"test": run_test, "status": run_status}.get(args.command, run_watch)
    asyncio.run(action(settings))


if __name__ == "__main__":
    cli()
