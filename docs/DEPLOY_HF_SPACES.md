# Deploy — Hugging Face Spaces (fully free)

One public URL, HTTPS included, 16GB RAM, no credit card. The Space runs a
single container: FastAPI serves both the API and the built frontend.

URL after deploy: `https://<your-hf-username>-urban-flood-nowcast.hf.space`

---

## STEP 0 — Prerequisites (on your PC)

1. Docker Desktop installed **and running**.
2. Git + Git Bash.
3. A Hugging Face account → sign up at https://huggingface.co/join (free).
4. The local app verified once (`/ready` all READY, LIVE/SCENARIO work in browser).

---

## STEP 1 — Create the Space (browser)

1. Go to https://huggingface.co/new-space
2. **Space name:** `urban-flood-nowcast`
3. **SDK:** Docker → **Blank** template
4. **Visibility:** Public (required for free hosting)
5. Create Space. Note the git URL shown on the page:
   `https://huggingface.co/spaces/<username>/urban-flood-nowcast`

---

## STEP 2 — Create an access token (browser)

1. https://huggingface.co/settings/tokens → **Create new token**
2. Type: **Write** → create → copy it (starts `hf_...`).

---

## STEP 3 — Build a clean upload directory (Git Bash, repo root)

```bash
mkdir -p /tmp/space
# copy only what the container needs (no venv, no node_modules, no .git)
cp deploy/hf/Dockerfile  /tmp/space/Dockerfile
cp deploy/hf/README.md   /tmp/space/README.md
cp deploy/hf/.dockerignore /tmp/space/.dockerignore
cp -r backend /tmp/space/backend
rm -rf /tmp/space/backend/venv /tmp/space/backend/__pycache__ /tmp/space/backend/water_monitor.db
mkdir -p /tmp/space/backend/app/data
cp -r backend/app/data /tmp/space/backend/app/data   # DEM + Mumbai + Delhi roads (in git)
cp -r scripts /tmp/space/scripts
cp main.py /tmp/space/main.py
cp -r frontend /tmp/space/frontend
rm -rf /tmp/space/frontend/node_modules /tmp/space/frontend/dist
cp -r data /tmp/space/data          # 612MB evidence data — takes a minute
```

## STEP 4 — Push to the Space (first push takes 15–45 min: 612MB + LFS)

```bash
cd /tmp/space
git init
git lfs install
git lfs track "data/**" "backend/app/data/**"
git add .gitattributes .dockerignore Dockerfile README.md main.py backend scripts frontend data
git commit -m "Deploy Urban Flood Nowcast"

git remote add space https://huggingface.co/spaces/<USERNAME>/urban-flood-nowcast
git push --force space main
# Username: <your HF username>
# Password: paste the hf_... WRITE token
```

HF's tracker will show upload progress; after upload the Space **builds**
(~10 min, watch the logs in the browser) then runs.

## STEP 5 — Verify

1. Space page → status **Running**, open the URL.
2. `/ready` should show all checks READY:
   `https://<username>-urban-flood-nowcast.hf.space/ready`
3. Click through: LIVE → NOW/+1h/+2h/+3h → MODEL SCENARIO 40/70 mm/h →
   SAFE ROUTE → HISTORICAL REPLAY → back to LIVE.

## STEP 6 — Later updates (code only, fast)

```bash
# edit code, then:
cp <changed files> /tmp/space/<same path>
cd /tmp/space && git add -A && git commit -m "Update" && git push space main
```

---

## Notes & limits (free tier)

- **Sleeps after ~48h without visits**; a visitor wakes it (~1–2 min cold
  start). Open the link before your demo.
- 50GB ephemeral disk, 16GB RAM — fits this app comfortably.
- The 612MB `data/` travels **inside** the Space repo via Git LFS (free).
- The Space DB (SQLite) is **ephemeral** — sensor-ingest demo data resets on
  restart. The Delhi/Mumbai model data is baked in the image and persists.
- Public Space = public code. Fine for SIH; ask if you want it private (needs
  a paid tier or a token-gated mirror).
