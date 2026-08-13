# joy-bot

Nvidia Founders Edition stock watcher — polls `api.store.nvidia.com` and sends a Telegram alert the moment a tracked SKU flips from out-of-stock to in-stock.

## Setup (local)

```bash
uv sync
cp .env.example .env      # then paste your TELEGRAM_TOKEN
make test                 # 11 tests, no network
make dry                  # live Nvidia poll, no real Telegram send
make run                  # live poll + real Telegram alerts
```

## Setup (server, Docker)

```bash
cp .env.example .env      # edit TELEGRAM_TOKEN
docker compose up -d --build
docker compose logs -f
```

State persists at `./data/state.json` (host) → `/data/state.json` (container).

## Config (env vars)

| Var | Default | Notes |
|---|---|---|
| `TELEGRAM_TOKEN` | — | required, from @BotFather |
| `TELEGRAM_CHAT_ID` | — | required |
| `LOCALE` | `fr-fr` | Nvidia storefront locale |
| `POLL_INTERVAL` | `45` | seconds between polls |
| `POLL_JITTER` | `10` | random 0–N s added per poll |
| `STATE_FILE` | `/data/state.json` | last-seen availability per SKU |
| `DRY_RUN` | `false` | log alerts, don't send |
| `LOG_LEVEL` | `INFO` | |

All Nvidia FE GPUs on the FR marketplace are auto-discovered (currently 5090, 5080, 5070). **No 5070 Ti FE exists** — Nvidia never released one, so it can't be tracked.

## Notes

- **TLS fingerprinting:** Nvidia is behind Akamai, which resets connections from plain `curl`/`httpx`. We use `curl_cffi` with Chrome impersonation to defeat this — no proxy or paid service needed.
- **Endpoint:** `api.nvidia.partners/edge/product/search` (returns `prdStatus` per product). We treat `buy_now` and `in_stock` as available.
- Rate limit is self-imposed (45s + jitter). Do not lower below 30s.
- Alerts fire only on out→in transitions, so a persistent drop won't spam you.
