# GitHub Clone-and-Run Audit for SIH Application

## 1. Required Prerequisites

### Backend
- **Python**: Version 3.14 (inferred from `backend/venv/pyvenv.cfg`)
  - Source: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/venv/pyvenv.cfg`
- **Packages**: Listed in `backend/requirements.txt`
  - fastapi>=0.111,<1.0
  - uvicorn[standard]>=0.30,<1.0
  - sqlalchemy>=2.0,<3.0
  - pydantic>=2.7,<3.0
  - pydantic-settings>=2.0,<3.0
  - numpy>=2.1,<3.0
  - scikit-learn>=1.5,<2.0
  - pandas>=2.2,<3.0
  - websockets>=12
  - python-dotenv>=1.0
  - httpx>=0.27,<1.0
  - pytest>=8.0,<9.0
  - pytest-asyncio>=0.23,<1.0
  - Source: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/requirements.txt`

### Frontend
- **Node.js**: Version 24.x (inferred from `@types/node`: "^24.13.3" in devDependencies)
  - Source: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/frontend/package.json`
- **Packages**: Listed in `frontend/package.json`
  - Dependencies:
    - maplibre-gl: ^6.7.0
    - react: ^19.2.8
    - react-dom: ^19.2.8
  - DevDependencies:
    - @types/node: ^24.13.3
    - @types/react: ^19.2.18
    - @types/react-dom: ^19.2.7
    - @vitejs/plugin-react: ^6.1.0
    - oxlint: ^1.79.0
    - typescript: ~6.0.2
    - vite: ^8.2.2
  - Source: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/frontend/package.json`

## 2. Files/Data Assets That Must Be Committed

The following files and directories are part of the repository and must be present for the application to run:

### Backend
- `backend/requirements.txt`
- `backend/main.py` (entry point)
- `backend/app/` (entire application structure)
- `backend/database.py` (SQLite setup)
- `backend/app/config.py` (configuration)
- `backend/app/data/` (contains all required data files):
  - `dem/mumbai_pilot_dem_30m.tif` (Digital Elevation Model)
  - `mumbai_pilot_osm_raw.json` (OpenStreetMap data)
  - `roads/mumbai_pilot_roads.geojson`
  - `roads/mumbai_pilot_intersections.geojson`
  - `drainage/bmc/storm_water_manholes_pilot.geojson` (BMC manholes)
  - `drainage/bmc/storm_water_drains_pilot.geojson` (BMC drains)
- `backend/venv/` (virtual environment) - **NOTE**: This is typically not committed, but the `requirements.txt` is. The venv is created on setup.

### Frontend
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/src/` (entire React application)
- `frontend/public/` (if exists, for static assets)

### Root Level
- `main.py` (alternative entry point that bootstraps sys.path and runs backend)
- `run_backend.bat` (Windows batch script to start backend)
- `README.md` files (documentation)
- Various markdown files (FRONTEND_DESIGN_PLAN.md, PHASE_2_0_BMC_INTEGRATION_SUMMARY.md, PROJECT_STATUS.md, RESEARCH_NOTES.md, si_h_flood_nowcasting_research.md)

## 3. External Downloads Currently Required

During runtime, the application makes external API calls and loads data:

### External API Dependencies
- **Open-Meteo API**: Used for rainfall nowcasting (0-3h forecast)
  - Endpoint: `https://api.open-meteo.com/v1/forecast`
  - Used in: `backend/app/infrastructure/rainfall/open_meteo.py`
  - No API key required (as of current implementation)
  - Source: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/app/infrastructure/rainfall/open_meteo.py`

- **Tile Server**: Used for map visualization in frontend
  - URL: `https://tiles.openfreemap.org/styles/liberty/{z}/{x}/{y}.png`
  - Used in: `frontend/src/components/FloodMap.tsx`
  - Source: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/frontend/src/components/FloodMap.tsx`

### Data Files (Already Committed)
The following data files are committed in the repository and do not require external download:
- Digital Elevation Model (DEM): `backend/app/data/dem/mumbai_pilot_dem_30m.tif`
- OpenStreetMap (OSM) raw data: `backend/app/data/mumbai_pilot_osm_raw.json`
- BMC (Brihanmumbai Municipal Corporation) drainage data:
  - Manholes: `backend/app/data/drainage/bmc/storm_water_manholes_pilot.geojson`
  - Drains: `backend/app/data/drainage/bmc/storm_water_drains_pilot.geojson`
- Road network data:
  - Roads: `backend/app/data/roads/mumbai_pilot_roads.geojson`
  - Intersections: `backend/app/data/roads/mumbai_pilot_intersections.geojson`

## 4. Environment Variables Required

The application uses Pydantic Settings to load environment variables from a `.env` file (if present). The following variables can be configured:

### Backend Environment Variables (from `backend/app/config.py`)
- `APP_NAME`: Application name (default: "Urban Flood Nowcasting System")
- `DEBUG`: Debug mode (default: False)
- `OPEN_METEO_TIMEOUT`: Timeout for Open-Meteo API calls in seconds (default: 10.0)
- `OPEN_METEO_CACHE_TTL_MINUTES`: Cache TTL for Open-Meteo data in minutes (default: 30)
- `MUMBAI_LAT`: Latitude for Mumbai (default: 19.0760)
- `MUMBAI_LON`: Longitude for Mumbai (default: 72.8777)
- `DEM_PATH`: Path to DEM file (automatically computed based on file location)
- `DATABASE_URL`: SQLite database URL (default: "sqlite:///./flood_nowcast.db")

To use environment variables, create a `.env` file in the backend directory (or root) with the desired values.
- Source: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/app/config.py`

### Frontend Environment Variables
- None required. The frontend does not read any environment variables (no usage of `import.meta.env` or `process.env` found).
  - Source: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/frontend/src/components/FloodMap.tsx` (and absence of .env files)

## 5. Exact Commands Needed to Run Backend + Frontend

### Backend
From the repository root:
```bash
# Option 1: Using the provided batch script (Windows)
run_backend.bat

# Option 2: Direct Python execution
python main.py

# Option 3: Using uvicorn directly (if venv activated)
# First, create and activate virtual environment:
python -m venv venv
venv\Scripts\activate
# Then install dependencies:
pip install -r backend/requirements.txt
# Finally, run:
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
From the repository root:
```bash
# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# To build for production
npm run build

# To preview production build
npm run preview
```

**Note**: The frontend expects the backend to be running on `http://localhost:8000`. Ensure the backend is started before or alongside the frontend.

## 6. Anything Preventing a Fresh-Machine Clone-and-Run

### Potential Issues
1. **Python Version**: The project requires Python 3.14. If the user has a different version, they may need to install Python 3.14 or use a version manager (like pyenv).
2. **Virtual Environment**: The `backend/venv/` directory is not committed (as expected). Users must create a virtual environment and install dependencies.
3. **Environment Variables**: While not strictly required (defaults are provided), users may want to configure a `.env` file for customization.
4. **Data Files**: All required data files (DEM, OSM, BMC, road networks) are committed in the repository, so no external download is needed for these.
5. **External API Access**: The application requires internet access to:
   - Open-Meteo API (for rainfall forecasts)
   - OpenFreeMap tile server (for map tiles)
   If the machine is behind a firewall that blocks these domains, the application will not function correctly.
6. **SQLite Database**: The database file `water_monitor.db` will be created automatically on first run in the backend directory.
7. **Frontend-Backend Communication**: The frontend makes API calls to `http://localhost:8000`. If the backend is not running or is on a different port/host, the frontend will not work.

### Missing Elements
- No `docker-compose.yml` or Dockerfile is provided for containerized deployment.
- No explicit `pyproject.toml` or `setup.py` for Python packaging (relies on `requirements.txt`).
- No version file (like `VERSION` or `__version__.py`) to specify application version.

## 7. Smallest Setup Automation We Should Implement

To enable a smooth clone-and-run experience, we recommend adding the following automation:

### Backend Automation
1. **Create a `setup.py` or `pyproject.toml`** for easier dependency installation (though `requirements.txt` is sufficient).
2. **Add a script to `backend/package.json`** (if we want to standardize) or enhance the existing `run_backend.bat` with a cross-platform script (e.g., using `package.json` scripts).
3. **Consider adding a `.env.example` file** showing the environment variables that can be configured.

### Frontend Automation
- Already has good npm scripts (`dev`, `build`, `preview`). No changes needed.

### Root Level Automation
1. **Add a root-level `package.json`** with workspace scripts to start both backend and frontend concurrently (e.g., using `concurrently` or `npm-run-all`).
   - Example scripts:
     ```json
     {
       "name": "sih-flood-nowcasting",
       "private": true,
       "version": "0.1.0",
       "scripts": {
         "install-all": "cd backend && pip install -r requirements.txt && cd ../frontend && npm install",
         "dev": "concurrently \"cd backend && python main.py\" \"cd frontend && npm run dev\"",
         "build": "cd frontend && npm run build",
         "preview": "cd frontend && npm run preview"
       },
       "devDependencies": {
         "concurrently": "^8.0.0"
       }
     }
     ```
2. **Ensure the `.gitignore` file** excludes the virtual environment (`backend/venv/`), the SQLite database (`water_monitor.db`), and any OS-specific files.
3. **Add a `README.md`** (if not already present) with clear clone-and-run instructions.

### Immediate Steps (Without Changing Code)
Since we are not allowed to change the code, we can only document the steps. However, for future development, the above automation would be beneficial.

## Sources

- Backend requirements: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/requirements.txt`
- Backend config: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/app/config.py`
- Backend main: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/main.py`
- Backend database: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/database.py`
- Backend Open-Meteo adapter: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/app/infrastructure/rainfall/open_meteo.py`
- Frontend package: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/frontend/package.json`
- Frontend FloodMap: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/frontend/src/components/FloodMap.tsx`
- Backend venv config: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/backend/venv/pyvenv.cfg`
- Root main.py: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/main.py`
- Run backend batch: `file:///C:/Users/laksh/OneDrive/Desktop/sih2026/run_backend.bat`

---
*Captured: 2026-09-07*