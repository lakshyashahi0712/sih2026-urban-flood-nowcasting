# Urban Flood Nowcasting System

Evidence-constrained urban flood nowcasting for Indian cities, with two
systems in one repository:

- **Delhi / Kushak V2 (current, primary)** — a 0–3 hour ensemble nowcasting
  and historical-replay system for the Kushak Nallah catchment (Barapullah
  drainage system, South Delhi), built as an evidence-constrained digital
  twin. Every output carries provenance (OBSERVED / OFFICIAL / DERIVED /
  ASSUMED / PROVISIONAL / UNKNOWN) and the system never fabricates missing
  data.
- **Mumbai / Kurla V1 (legacy, frozen)** — the original Kurla pilot
  (terrain + BMC drainage + street intelligence + flood-safe routing).
  Preserved for reference; not under active development.

> **What this system is not:** it does not claim calibrated or validated
> flood-depth accuracy, street-level depth truth, or observed river stage.
> Where evidence is missing the outputs say UNKNOWN — see
> [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

---

## Quick start (local development)

Prerequisites: **Python 3.12+** and **Node.js 20+**.

### 1. Backend

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (Git Bash: source venv/Scripts/activate)
pip install -r backend/requirements.txt
python main.py                   # serves http://localhost:8000
```

`python main.py` from the repository root (or `run_backend.bat` on Windows)
starts the FastAPI app. Docs: <http://localhost:8000/docs>.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                      # serves http://localhost:5173
```

The Vite dev server proxies `/api`, `/flood`, `/rainfall`, `/routing`,
`/health`, and `/ready` to `http://localhost:8000` (override the target
with the `VITE_API_TARGET` environment variable).

Open <http://localhost:5173> — the app starts on **DELHI V2**.

### 3. One-command alternative (root scripts)

```bash
npm run install-all              # backend pip + frontend npm install
npm run dev                      # backend + frontend together (concurrently)
```

---

## Evidence data (required for Delhi V2 features)

The `data/` tree — raw and derived evidence for the Kushak digital twin
(catalogues, forcing hyetographs, DEM derivatives, GeoJSON layers) — is
**acquired locally and not committed** (see `.gitignore`). Without it:

- `/ready` reports the affected components `NOT_READY` (named checks),
- the Delhi events/replay endpoints return 503/empty responses,
- the map serves no Delhi layers.

With the data tree present, verify integrity end-to-end:

```bash
python scripts/generate_phase15_replay.py   # Phase 15.5 replay → FINAL_VERDICT
```

## Tests

```bash
# Delhi scientific domain suite (co-located with the core)
python -m pytest backend/app/domain/delhi -q

# Backend API + legacy suite
python -m pytest backend/tests -q
```

Both suites are green (1045 tests at release). CI runs them on every push
(`.github/workflows/ci.yml`), together with the frontend type-check/build
and the replay integrity check when the evidence data is present.

## Docker deployment

```bash
docker compose up --build
# frontend: http://localhost:8080   backend: http://localhost:8000
```

The `data/` evidence tree is bind-mounted read-only into the backend
container. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Product surface

| View | What it shows |
| --- | --- |
| **NOWCAST** (Delhi) | Live 0–3h Open-Meteo NWP forcing for the documented Safdarjung reference point, the 6-member deterministic ensemble inflow/storage envelope, and per-reach model states — with explicit UNKNOWN labels where the science has no defensible answer |
| **REPLAY** (Delhi) | The six catalogued historical events; executable events (EVT-2024-06-27, EVT-2023-07-08) run the genuine hydraulic runtime with forcing resolution preserved, including timestep playback, per-reach mass balance, and integrity checks |
| **EVIDENCE** (Delhi) | The locked reach chain with evidence tiers, the deterministic ensemble definition with parameter provenance, and the system's explicit non-claims |
| **Mumbai V1** | The frozen Kurla pilot (forecast horizons, scenarios, 2017 replay, street intelligence, safe routing) |

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system architecture
- [docs/API_DELHI_V2.md](docs/API_DELHI_V2.md) — Delhi V2 API reference
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) — operator/user guide
- [docs/LIMITATIONS.md](docs/LIMITATIONS.md) — known limitations & non-claims
- [docs/DATA_PROVENANCE_MATRIX.md](docs/DATA_PROVENANCE_MATRIX.md) — evidence provenance
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — deployment guide
- [docs/DELHI_KUSHAK_PHASE15_5_TRUE_RUNTIME_REPLAY.md](docs/DELHI_KUSHAK_PHASE15_5_TRUE_RUNTIME_REPLAY.md) — replay contract
- [docs/archive/](docs/archive/) — superseded working notes (historical only)
