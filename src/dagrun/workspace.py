from __future__ import annotations

from pathlib import Path
from typing import Optional


def find_project_root(start: Path) -> Path:
    """
    Find a reasonable "project root" for storing DAGrun artifacts.

    Rules (deterministic):
    - Walk upward from `start` (file path or directory).
    - If a `.git/` directory is found, that directory is the root.
    - Otherwise, return the starting directory (or the parent directory of a file).
    """
    p = start
    if p.is_file():
        p = p.parent

    cur: Optional[Path] = p
    while cur is not None:
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return p


def ensure_dagrun_dir(project_root: Path) -> Path:
    d = project_root / ".dagrun"
    d.mkdir(parents=True, exist_ok=True)
    return d

