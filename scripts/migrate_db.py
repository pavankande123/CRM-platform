"""
Enermax CRM - Database Migration Runner Script
Executes Alembic migrations to upgrade the schema to the latest revision.
"""
import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command


def run_migrations():
    alembic_ini_path = backend_dir / "alembic.ini"
    if not alembic_ini_path.exists():
        print(f"Error: Could not locate alembic.ini at {alembic_ini_path}", file=sys.stderr)
        sys.exit(1)

    print("Running database migrations (upgrade head)...")
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    
    try:
        command.upgrade(alembic_cfg, "head")
        print("Database migrations applied successfully.")
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
