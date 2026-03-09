from __future__ import annotations
from pathlib import Path
from datetime import datetime
import shutil

def backup_sqlite(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = backup_dir / f"bd_crm_backup_{ts}.sqlite"
    shutil.copy2(db_path, dst)
    return dst