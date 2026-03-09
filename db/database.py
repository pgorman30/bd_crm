from __future__ import annotations

import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DEFAULT_ONEDRIVE_SUBPATH = Path("OneDrive") / "BD_CRM" / "data" / "bd_crm.sqlite"


def _default_db_path() -> Path:
    """
    Picks a sensible default in the user's home directory.
    Works for Mac/Windows if OneDrive is installed and syncing.
    You can override with env var BD_CRM_DB_PATH.
    """
    env = os.getenv("BD_CRM_DB_PATH")
    if env:
        return Path(env).expanduser()

    home = Path.home()
    # Common OneDrive locations:
    candidates = [
        home / DEFAULT_ONEDRIVE_SUBPATH,
        home / "OneDrive - Novoprotein" / "BD_CRM" / "data" / "bd_crm.sqlite",
        home / "OneDrive - NovoProtein" / "BD_CRM" / "data" / "bd_crm.sqlite",
        home / "OneDrive - Personal" / "BD_CRM" / "data" / "bd_crm.sqlite",
        home / "OneDrive" / "BD_CRM" / "data" / "bd_crm.sqlite",
    ]
    for c in candidates:
        # choose first parent that exists, else fall back to home/OneDrive path
        if c.parent.exists():
            return c

    # fallback: create under home
    return home / DEFAULT_ONEDRIVE_SUBPATH


def get_engine():
    db_path = _default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )

    # Pragmas: WAL improves robustness with sync folders (still: don't run both machines at once)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("PRAGMA synchronous=NORMAL;"))
        conn.execute(text("PRAGMA foreign_keys=ON;"))
        conn.commit()

    return engine, db_path


ENGINE, DB_PATH = get_engine()
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)