# Deployment Guide

## Free public hosting (2026)

> Hugging Face Spaces dropped free Docker/Gradio in July 2026 — free accounts
> can create **Static Spaces only** (no backend), so HF cannot host this app.
> Render/Railway/Fly free tiers also don't fit (512MB RAM / credits / sleep).
> `deploy/hf/Dockerfile` remains useful as the **single-container build**
> (FastAPI serving the built frontend) reused by the options below.

| Option | Cost | URL stability | Backend runs on | Best for |
|---|---|---|---|---|
| 0. Azure for Students B1s | ₹0 for 12 mo, no card | permanent IP, 24/7 | real VM | **submitted link (recommended)** |
| 1. ngrok static domain | ₹0 | stable `xxx.ngrok-free.app` | your PC | demo link you can share today |
| 2. Cloudflare quick tunnel | ₹0 | random URL, changes per run | your PC | 2-minute throwaway demo |
| 3. Oracle Cloud Always Free VM | ₹0 forever | your domain/IP, never sleeps | real VPS | permanent link (needs card to verify) |
| 4. Google Cloud Run free tier | ₹0 within limits | permanent, scale-to-zero | managed container | permanent, ~1 min cold start |

### Option 0 — Azure for Students B1s VM (no credit card, 24/7, for the submitted link)

Azure for Students gives $100 credit + 12 months of free services with
**no credit card** — signup is verified by a college email (or the GitHub
Student Developer Pack). The 12-month free tier includes a **B1s VM
(750 hrs/month = always on) at zero charge**, so the $100 stays as buffer.

1. Sign up: https://azure.microsoft.com/free/students → **Azure for
   Students** → verify college email. No card anywhere in the flow.
2. Portal → **Create a resource → Virtual machine**:
   - Image: **Ubuntu 24.04 LTS**; Size: **B1s** (1 vCPU / 1 GB — free tier);
   - Inbound ports: allow **SSH (22)** and **HTTP (8080)**;
   - Region: Central India (closest to judges).
3. SSH in and bootstrap (docker, 2 GB swap, repo, compose):
   ```bash
   ssh azureuser@<VM_IP>
   git clone -b v2-recovery-parity \
     https://github.com/lakshyashahi0712/sih2026-urban-flood-nowcasting.git /opt/app
   cd /opt/app && sudo bash scripts/dev/vm_bootstrap.sh
   ```
   The script prints the exact `scp` command to run **from your PC** to fill
   the 612MB `data/` tree, then relaunch with it.
4. Submit `http://<VM_IP>:8080`.

Notes: 1 GB RAM is tight — the bootstrap adds 2 GB swap, which absorbs the
flood pipeline's peak; if it ever OOMs under judging load, resize to B2s
(~$9/mo, paid from the $100 credit → still ~11 months covered). The student
subscription has a built-in spending limit, so accidental overuse cannot
bill you. Do NOT enable auto-shutdown on the VM.

### Option 1 — ngrok static domain (recommended demo path)

1. Sign up free at https://ngrok.com → dashboard shows an authtoken.
2. Claim a **free static domain** (dashboard → Domains → every free account
   gets one, e.g. `salmon-aware-crappie.ngrok-free.app`).
3. Build the single-container image and run it (or just run uvicorn + built
   frontend directly):
   ```bash
   docker build -f deploy/hf/Dockerfile -t floodnow .
   docker run -p 7860:7860 floodnow          # serves frontend + API
   ```
4. Expose it:
   ```bash
   ngrok config add-authtoken <YOUR_TOKEN>
   ngrok http --url=<your-static-domain> 7860
   ```
5. Share `https://<your-static-domain>` — HTTPS included, works on phones.

The link is stable, but it only answers while your PC runs the container.
Start it again before the demo. (ngrok free shows an interstitial warning
page to first-time browser visitors; a click passes through. API calls from
the SPA are unaffected.)

### Option 2 — Cloudflare quick tunnel (no account)

```bash
# one-time: download cloudflared (winget install Cloudflare.cloudflared)
docker run -p 7860:7860 floodnow
cloudflared tunnel --url http://localhost:7860
```
Prints a random `https://<words>.trycloudflare.com` URL. No signup, but the
URL changes every run — good for a live demo, not for a printed report.

### Option 3 — Oracle Cloud Always Free VM (permanent, ₹0 forever)

1. https://www.oracle.com/cloud/free/ → sign up (card needed to verify,
   never charged on Always Free).
2. Create an **Ampere A1 VM** (up to 4 OCPU / 24GB free forever), Ubuntu 24.04,
   allow `TCP 80/443/22` in the VCN security list **and** the OS firewall.
3. On the VM:
   ```bash
   curl -fsSL https://get.docker.com | sh
   git clone -b <branch> https://github.com/lakshyashahi0712/sih2026-urban-flood-nowcasting.git app
   # copy the 612MB data/ tree up (from your PC):
   #   scp -r data/* user@VM_IP:~/app/data/
   cd app && docker compose up -d --build
   ```
4. Open `http://VM_IP:8080` (compose) or front it with Caddy for HTTPS.

No sleep, no quota — the real permanent answer if signup cooperates
(ARM capacity is sometimes waitlisted in busy regions; retry or pick
another home region).

### Option 4 — Google Cloud Run free tier (permanent, serverless)

The single-container build deploys as-is; 2M requests/month are free.
Cold start after idle is ~30–60s (heavy first-hit simulation can be slower
on a cold container; the first LIVE request warms the caches).

```bash
gcloud run deploy floodnow --source . --dockerfile deploy/hf/Dockerfile \
  --memory 4Gi --cpu 2 --timeout 300 --allow-unauthenticated --region asia-south1
```
Card needed at signup (free-tier only, never auto-charged without warning).

### What does NOT work free

- Hugging Face Spaces (static-only on free since Jul 2026), GitHub Pages,
  Vercel/Netlify — no Python backend.
- Render / Railway / Fly free — RAM too small (rasterio + numpy sim),
  sleep/credits.
- Any serverless CPU under ~2GB RAM — the flood pipeline needs more.

---

## Local development (recommended for operation)

```bash
python -m venv venv && venv\Scripts\activate     # Windows
pip install -r backend/requirements.txt
python main.py                                   # backend :8000

cd frontend && npm install && npm run dev        # frontend :5173
```

The Vite dev server proxies API calls to `http://localhost:8000`
(configurable via `VITE_API_TARGET`).

## Production build (single host)

```bash
cd frontend && npm run build          # emits frontend/dist
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1
```

When `frontend/dist` exists, `backend.main:app` **serves it directly**
(single-container mode): `/` and `/index.html` return the SPA, all API
routes keep precedence. This is how the free-hosting options above run
without a separate nginx.

Serve `frontend/dist` with any static server that proxies
`/api /flood /rainfall /routing /health /ready` to the backend —
`frontend/nginx.conf` is a ready-made configuration.

## Docker Compose

```bash
docker compose up --build
# frontend  http://localhost:8080  (nginx, reverse-proxies the API)
# backend   http://localhost:8000  (FastAPI, healthcheck on /ready)
```

- `data/` (the locally-acquired evidence tree) is bind-mounted read-only
  into the backend. It is intentionally **not** baked into the image.
- If `data/` is absent, the backend still starts; `/ready` reports the
  affected Delhi components `NOT_READY` by name, and Delhi endpoints
  degrade explicitly (never with fabricated data).

## Configuration

| Setting | Where | Default |
| --- | --- | --- |
| Backend port | `python main.py` / uvicorn | `8000` |
| API proxy target (dev) | `VITE_API_TARGET` env | `http://localhost:8000` |
| Extra CORS origins | `FLOOD_EXTRA_ORIGINS` env (comma-separated) | localhost:5173/4173 |
| Nowcast reference point | `backend/app/domain/delhi/nowcast.py` (`SAFDARJUNG_LAT/LON`) | documented Safdarjung station |
| Forecast cache TTL | `nowcast.CACHE_TTL_MINUTES` | 15 min |
| Frontend dev port | Vite | `5173` |
| Compose frontend port | `docker-compose.yml` | `8080` |

## Health & readiness

- `GET /health` — liveness (`{"status": "ok"}`).
- `GET /ready` — named component checks: `delhi_router_import`,
  `delhi_event_catalog`, `delhi_geo_layers`, `mumbai_dem`, `database`.
  Overall `READY` only when all pass. Use this for orchestrator
  probes; it never collapses failures into a single anonymous boolean.

## Operational notes

- The nowcast endpoint polls Open-Meteo per request with a 15-minute
  server-side cache; failed refreshes fall back to the cached fetch
  marked `STALE`. No feed access → explicit `UNAVAILABLE`/`BLOCKED`
  responses (HTTP 200 with honest states, so dashboards can render
  them).
- The replay endpoints execute the deterministic runtime (~seconds);
  responses are cached in-process. `?refresh=true` forces re-execution.
- CORS is restricted to localhost dev origins plus `FLOOD_EXTRA_ORIGINS`
  (the previous `*` + credentials combination was invalid per spec).
- Logs: uvicorn access logs plus structured domain diagnostics; no
  secrets are involved (the app requires no API keys).
