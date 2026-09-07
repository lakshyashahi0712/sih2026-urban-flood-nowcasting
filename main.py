from __future__ import annotations
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
_backend = _root / "backend"
for _p in [str(_root), str(_backend)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
