import sys
import os
import shutil
from pathlib import Path

# Add backend directory to sys.path so app modules can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure SQLite database is copied to /tmp so it is writeable in Vercel Serverless
TMP_DB = Path("/tmp/enermax_dev.db")
SOURCE_DB = BACKEND_DIR / "enermax_dev.db"

# If in serverless environment (/tmp exists and is writeable)
if os.path.exists("/tmp") and SOURCE_DB.exists():
    if not TMP_DB.exists():
        shutil.copy2(SOURCE_DB, TMP_DB)
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////tmp/enermax_dev.db"
elif SOURCE_DB.exists():
    os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{SOURCE_DB.as_posix()}")

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("TOKEN_BLACKLIST_ENABLED", "false")

from app.main import app
