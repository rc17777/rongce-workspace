"""Shared paths for the Rongce RAG and Obsidian Wiki tools."""
from __future__ import annotations

import os
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
INDEX_DIR = WORKSPACE / ".rag_index"
INDEX_FILE = INDEX_DIR / "rag_index.json"
CHUNKS_FILE = INDEX_DIR / "chunks.json"

OBSIDIAN_VAULT = Path(
    os.environ.get("RONGCE_OBSIDIAN_VAULT", r"C:\Users\scrccpa\Documents\Obsidian Vault")
)

# Keep the old D: vault as a read-only source when it exists. The unified entry
# point is this OpenClaw workspace; source documents may still live elsewhere.
KNOWLEDGE_DIRS = [
    WORKSPACE / "knowledge",
    OBSIDIAN_VAULT,
]

LEGACY_OBSIDIAN_VAULT = Path(r"D:\openclaw-workspace\obsidian-vault")
if LEGACY_OBSIDIAN_VAULT.exists() and LEGACY_OBSIDIAN_VAULT not in KNOWLEDGE_DIRS:
    KNOWLEDGE_DIRS.append(LEGACY_OBSIDIAN_VAULT)


def existing_knowledge_dirs() -> list[Path]:
    return [path for path in KNOWLEDGE_DIRS if path.exists()]


def ensure_index_dir() -> Path:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return INDEX_DIR
