from pathlib import Path
import os

# Root directory of the repository (three levels up from this file: app/config/paths.py -> app/config -> app -> ROOT)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOG_DIR = ROOT_DIR / "log"

# Convenience: ensure common directories exist in local/dev runs (no-op if created elsewhere)
for _d in (DATA_DIR, RAW_DIR, PROCESSED_DIR, LOG_DIR):
    try:
        _d.mkdir(parents=True, exist_ok=True)
    except Exception:
        # If running in an environment where creation isn't desired (CI, containers managed externally), ignore
        pass
