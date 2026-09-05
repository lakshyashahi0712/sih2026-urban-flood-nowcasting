
"""Root entrypoint for AquaSense / Urban Flood Nowcasting API."""
import os
import sys
from pathlib import Path

# Add both repository root and backend directory to sys.path
_repo_root = Path(__file__).resolve().parent
_backend_dir = _repo_root / "backend"
for _p in [str(_backend_dir), str(_repo_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
