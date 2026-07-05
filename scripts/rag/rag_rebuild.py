"""重建融策 RAG 索引（workspace knowledge + Obsidian Vault）。"""
from __future__ import annotations

import os
import pickle
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from rag_config import INDEX_FILE, ensure_index_dir, existing_knowledge_dirs


def read_md_files(dirs):
    files = []
    for root in dirs:
        for dirpath, _, filenames in os.walk(root):
            skip = [".git", "__pycache__", "node_modules", ".obsidian"]
            if any(s in dirpath for s in skip):
                continue
            for fn in filenames:
                if fn.endswith(".md") and not fn.startswith("."):
                    fp = os.path.join(dirpath, fn)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="replace") as f:
                            text = f.read()
                    except OSError:
                        continue
                    if len(text) < 100:
                        continue
                    rel = os.path.relpath(fp, root)
                    files.append((rel, text, str(root)))
    return files


def chunk_text(text, rel_path, root_label="", max_chars=500):
    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) < max_chars:
            current = current + "\n\n" + para if current else para
        else:
            if current and len(current) > 50:
                chunks.append({"text": current, "source": rel_path, "label": root_label})
            current = para
    if current and len(current) > 50:
        chunks.append({"text": current, "source": rel_path, "label": root_label})
    return chunks


ensure_index_dir()
knowledge_dirs = existing_knowledge_dirs()
print("Scanning directories...")
for path in knowledge_dirs:
    print(f"  - {path}")

files = read_md_files(knowledge_dirs)
print(f"Found {len(files)} .md files")

all_chunks = []
for rel, text, label in files:
    all_chunks.extend(chunk_text(text, rel, label))

print(f"Total chunks: {len(all_chunks)}")

from sklearn.feature_extraction.text import TfidfVectorizer

texts = [c["text"] for c in all_chunks]

print("Building TF-IDF index...")
vectorizer = TfidfVectorizer(
    max_features=15000,
    ngram_range=(1, 2),
    analyzer="char_wb",
    max_df=0.8,
    min_df=2,
)
tfidf_matrix = vectorizer.fit_transform(texts)
print(f"TF-IDF matrix: {tfidf_matrix.shape}")

with open(INDEX_FILE, "wb") as f:
    pickle.dump(
        {
            "vectorizer": vectorizer,
            "matrix": tfidf_matrix,
            "chunks": all_chunks,
            "texts": texts,
        },
        f,
    )
print(f"Index saved: {INDEX_FILE}")
print(f"\nDone! {len(all_chunks)} chunks indexed")
