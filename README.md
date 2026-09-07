# SIH Flood Nowcasting Application

## Prerequisites
- **Git** (to clone the repository)
- **Python 3.14** (backend)
- **Node.js 24.x** (frontend)

## Clone Instructions
```bash
git clone <repository-url>
cd sih2026
```

## Backend Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   ```bash
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Configure environment variables (optional):
   ```bash
   # Copy the example environment file
   copy backend\.env.example backend\.env
   # Edit .env to customize settings if needed
   ```

## Frontend Setup
1. Install dependencies:
   ```bash
   npm install
   ```

## Run Commands
### Backend
From the repository root:
```bash
# Using the provided batch script (Windows)
run_backend.bat

# Or directly
python main.py
```
The backend will run on `http://localhost:8000`.

### Frontend
From the repository root:
```bash
# Start development server
npm run dev
```
The frontend will be available at `http://localhost:5173` (or another port if 5173 is in use).

## Project Architecture
- **backend/**: FastAPI application with:
  - `main.py`: Entry point
  - `app/`: Application structure (routers, models, infrastructure)
  - `data/`: Bundled datasets (DEM, OSM, BMC, road networks)
  - `database.py`: SQLite setup
- **frontend/**: React + TypeScript + Vite application
  - `src/`: Source code
  - `components/FloodMap.tsx`: Map visualization using MapLibre GL

## Required Bundled Datasets
All data files are committed in the repository under `backend/app/data/`:
- Digital Elevation Model (DEM): `dem/mumbai_pilot_dem_30m.tif`
- OpenStreetMap (OSM) raw data: `mumbai_pilot_osm_raw.json`
- BMC (Brihanmumbai Municipal Corporation) drainage data:
  - Manholes: `drainage/bmc/storm_water_manholes_pilot.geojson`
  - Drains: `drainage/bmc/storm_water_drains_pilot.geojson`
- Road network data:
  - Roads: `roads/mumbai_pilot_roads.geojson`
  - Intersections: `roads/mumbai_pilot_intersections.geojson`

## Known Limitations
- Requires internet access for:
  - Open-Meteo API (rainfall nowcasting): `https://api.open-meteo.com/v1/forecast`
  - Map tiles: `https://tiles.openfreemap.org/styles/liberty/{z}/{x}/{y}.png`
- If behind a firewall that blocks these domains, the application will not function correctly.
- The SQLite database (`water_monitor.db`) is created automatically on first run in the backend directory.
- Environment variables can be configured via a `.env` file in the backend directory (see `backend/app/config.py` for details).