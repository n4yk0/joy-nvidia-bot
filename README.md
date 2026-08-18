# joy-bot — Nvidia GPU Stock Alerts on Telegram

A small program that watches Nvidia's French storefront for **RTX 5090 / 5080 / 5070 Founders Edition** drops and sends you a Telegram message the moment one is available to buy.

- **No spam.** Alerts fire only when a card goes from *out of stock* to *in stock*.
- **Runs quietly in the background** on any always-on computer (laptop, home server, Raspberry Pi, cheap cloud VPS).
- **Ask any time.** Send `/status` to your bot to see the current stock on demand.

---

## What you'll need

1. **A computer that stays on.** Any Windows PC, Mac, or Linux machine will do.
2. **Docker Desktop.** This is what actually runs the bot.
   - Windows / macOS: <https://www.docker.com/products/docker-desktop/> — download, install, then **open Docker Desktop at least once** so it starts running in the background.
   - Linux (Debian / Ubuntu): `sudo apt install docker.io docker-compose-v2`
   - **Windows only:** Docker Desktop needs **WSL2** to run containers. The Docker installer sets it up for you automatically — just accept the prompts and reboot if asked. If it fails, see the WSL2 note in [Troubleshooting](#troubleshooting).
3. **The Telegram app** on your phone.

You do **not** need to know Python, or install anything else. Everything runs inside Docker.

---

## Step 1 — Create your Telegram bot (2 minutes)

1. Open Telegram, tap the search icon, and search for **`@BotFather`** (the official one — it has a blue checkmark).
2. Open the chat and send `/newbot`.
3. Answer BotFather's two questions:
   - **Name:** anything you like, e.g. `My Nvidia Watcher`
   - **Username:** must end in `bot`, e.g. `mynvidia_watch_bot`
4. BotFather replies with a **token** that looks like `1234567890:AAH_abcdefgh...`. **Copy it and keep it private** — anyone with this token can control your bot.
5. In Telegram, search for your new bot by its username, open the chat, and **send it any message** (e.g. `hi`). This is required for step 2.

## Step 2 — Find your Telegram chat ID (30 seconds)

Open a web browser and paste this URL, replacing `<TOKEN>` with the token you just copied:

```
https://api.telegram.org/bot<TOKEN>/getUpdates
```

You'll see a page of text. Look for `"chat":{"id":123456789,...}`. That **number** is your chat ID. Copy it.

> If you see `"result":[]` (empty), you forgot step 1.5 — go back and send your bot a message, then refresh.

---

## Step 3 — Download the code

### Windows

1. Go to <https://github.com/BakeNayk0/joy-nvidia-bot>
2. Click the green **`< > Code`** button → **Download ZIP**
3. Right-click the downloaded ZIP → **Extract All…** — you'll get a folder called `joy-nvidia-bot-main`
4. Open the folder, then hold **Shift** and **right-click** on empty space → **Open PowerShell window here** (or **Open in Terminal** on Windows 11).

### macOS / Linux

Open a terminal and run:

```bash
git clone https://github.com/BakeNayk0/joy-nvidia-bot.git
cd joy-nvidia-bot
```

If you don't have `git`, download the ZIP the same way as Windows, extract, and `cd` into the folder.

---

## Step 4 — Configure

Inside the project folder you'll find a file called **`.env.example`**. You need to make a copy called **`.env`** and put your token + chat ID into it.

### Windows

1. In File Explorer, click **View → Show → File name extensions** (so you can see `.env.example` as its full name).
2. Copy `.env.example`, paste it in the same folder, and rename the copy to `.env` (yes, starting with a dot, no other name).
3. Right-click `.env` → **Open with → Notepad**.
4. Replace `123456789:replace-me` with your token, and `000000000` with your chat ID. Save and close.

### macOS / Linux

```bash
cp .env.example .env
nano .env         # or use any text editor
```

Fill in `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`, then save.

---

## Step 5 — Start the bot

In the terminal window you opened inside the project folder, run:

```bash
docker compose up -d --build
```

The first run takes 1–2 minutes (downloads dependencies + builds the image). After that it starts in the background.

### Confirm it's working

Open Telegram, go to your bot's chat, and send **`/status`**. Within a couple of seconds you should get back something like:

```
État du stock Nvidia FE
❌ NVIDIA RTX 5090 — €2,099.00
❌ NVIDIA RTX 5080 — €1,059.00
❌ NVIDIA RTX 5070 — €589.00

Canary — cartes partenaires (6/6 en stock)
✅ ASUS RTX 3050 — €252.99
✅ PNY RTX 5060 — €376.65
...
```

The ✅ partner cards prove the bot is seeing live Nvidia data.

---

## Daily use

### Commands you can send in the Telegram chat with your bot

| Send this | What happens |
|---|---|
| `/status` | Snapshot of current stock (Founders Edition + canary partners) |
| `/test` | Confirms the bot is running and can reach you |
| `/ping` | Same as `/test`, shorter reply |

You don't need to check anything actively — the bot will message you **automatically** the moment a 5090/5080/5070 Founders Edition becomes available.

### Terminal commands (run from the project folder)

| To do this | Run this |
|---|---|
| See live logs | `docker compose logs -f` (press Ctrl+C to stop watching) |
| Stop the bot | `docker compose down` |
| Restart the bot | `docker compose restart` |
| Update after pulling new code | `docker compose up -d --build` |

---

## Troubleshooting

**`docker: command not found`**
Docker Desktop isn't installed or isn't running. Open Docker Desktop from your Start menu / Applications and wait for the whale icon to say "Docker Desktop is running", then retry.

**Windows: Docker Desktop says "WSL 2 installation is incomplete" or won't start**
Open **PowerShell as Administrator** (Start menu → right-click PowerShell → *Run as administrator*) and run:
```powershell
wsl --install
```
Reboot when it finishes, then open Docker Desktop again. If `wsl --install` says virtualization is disabled, you need to enable it in your PC's BIOS/UEFI (look for **Intel VT-x**, **AMD-V**, or **SVM Mode**) — this varies by manufacturer, search "enable virtualization &lt;your PC model&gt;".

**Linux: `permission denied while trying to connect to the Docker daemon`**
Either prefix commands with `sudo`, or add your user to the docker group:
```bash
sudo usermod -aG docker $USER
```
Then log out and back in.

**`/status` gives no reply**
Check the container is actually running:
```bash
docker compose ps
```
If it says `Restarting`, something crashed. Inspect the logs:
```bash
docker compose logs --tail 30
```
Common causes:
- Wrong `TELEGRAM_TOKEN` in `.env` — recopy from BotFather.
- Wrong `TELEGRAM_CHAT_ID` — messages are silently dropped if the chat ID doesn't match.

**`fetch failed` in logs**
Nvidia may have changed something on their end. Try `docker compose restart` first. If it persists, open a GitHub issue.

**I want to watch a different country's storefront**
Edit `.env` and change `LOCALE=fr-fr` to e.g. `LOCALE=en-us`, then `docker compose up -d --build`. Note that SKU names and canary cards vary by region — some may not exist in every locale.

---

## For developers

<details>
<summary>Click to expand</summary>

Built with `uv` (Python 3.12+), `httpx`, `curl_cffi` (defeats Akamai TLS fingerprinting), `pydantic-settings`, `tenacity`.

### Local development

```bash
uv sync
cp .env.example .env
make test        # respx-mocked, no network
make dry         # live Nvidia poll, Telegram alerts logged instead of sent
make run         # live everything
make test-msg    # send a one-shot test message
make status      # push a one-shot stock snapshot
```

### Config reference

| Env var | Default | Purpose |
|---|---|---|
| `TELEGRAM_TOKEN` | — | required, from @BotFather |
| `TELEGRAM_CHAT_ID` | — | required |
| `LOCALE` | `fr-fr` | Nvidia storefront locale |
| `POLL_INTERVAL` | `45` | seconds between polls |
| `POLL_JITTER` | `10` | random 0–N s added per poll |
| `STATE_FILE` | `/data/state.json` | last-seen availability per SKU |
| `DRY_RUN` | `false` | log alerts, don't send |
| `LOG_LEVEL` | `INFO` | set `DEBUG` for per-tick output |
| `IMPERSONATE` | `chrome` | curl_cffi TLS profile |

### Design notes

- **TLS fingerprinting:** Nvidia is behind Akamai, which resets connections from plain `curl` / `httpx`. `curl_cffi` with Chrome impersonation defeats it. No proxy needed.
- **Endpoint:** `api.nvidia.partners/edge/product/search` — always returns per-product `prdStatus`, unlike `feinventory` which is empty when nothing is dropping.
- **Alerts on transitions only** (`out → in`), not on raw availability. Persistent drops don't spam.
- **Watch loop and Telegram command listener run concurrently** in one asyncio process; the listener uses `getUpdates` long-polling — no public URL needed.
- **Only Founders Edition cards trigger alerts.** Partner cards are shown in `/status` as a "canary" so you can visually verify the pipeline is live.

</details>
