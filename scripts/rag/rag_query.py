"""融策审计知识库 RAG 系统 - 本地检索 + 可选 AI 生成。"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from rag_config import INDEX_FILE, ensure_index_dir, existing_knowledge_dirs


def read_md_files(roots):
    files = []
    for root in roots:
        for dirpath, _, filenames in os.walk(root):
            skip_dirs = [".git", "__pycache__", "node_modules", ".obsidian"]
            if any(s in dirpath for s in skip_dirs):
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


def build_index():
    ensure_index_dir()
    roots = existing_knowledge_dirs()
    print("Building index for the first time...")
    print("Sources:")
    for root in roots:
        print(f"  - {root}")

    files = read_md_files(roots)
    print(f"Found {len(files)} .md files")

    all_chunks = []
    for rel, text, label in files:
        all_chunks.extend(chunk_text(text, rel, label))

    print(f"Total chunks: {len(all_chunks)}")

    from sklearn.feature_extraction.text import TfidfVectorizer

    texts = [c["text"] for c in all_chunks]
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
    return vectorizer, tfidf_matrix, texts, all_chunks


def load_index():
    if not INDEX_FILE.exists():
        return build_index()

    with open(INDEX_FILE, "rb") as f:
        data = pickle.load(f)
    vectorizer = data["vectorizer"]
    tfidf_matrix = data["matrix"]
    texts = data["texts"]
    all_chunks = data["chunks"]
    print(f"Loaded index: {len(all_chunks)} chunks, matrix {tfidf_matrix.shape}")
    print(f"Index file: {INDEX_FILE}")
    return vectorizer, tfidf_matrix, texts, all_chunks


vectorizer, tfidf_matrix, texts, all_chunks = load_index()


def search(query, top_k=5):
    q_vec = vectorizer.transform([query])
    from sklearn.metrics.pairwise import cosine_similarity

    scores = cosine_similarity(q_vec, tfidf_matrix)[0]
    top_idx = scores.argsort()[::-1][:top_k]
    results = []
    for idx in top_idx:
        if scores[idx] > 0.01:
            chunk = all_chunks[idx]
            results.append(
                {
                    "score": float(scores[idx]),
                    "source": chunk["source"],
                    "label": chunk.get("label", ""),
                    "text": chunk["text"][:500],
                }
            )
    return results


ZHIPU_API = os.environ.get("ZHIPU_API_KEY", "")
ZHIPU_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ZHIPU_MODEL = os.environ.get("ZHIPU_MODEL", "glm-4-plus")
if not ZHIPU_API:
    config_paths = [
        str(INDEX_FILE.parents[1] / ".openclaw" / "profile.json"),
        str(INDEX_FILE.parents[1] / "config" / "api_keys.json"),
    ]
    for cp in config_paths:
        if os.path.exists(cp):
            try:
                with open(cp, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                for k, v in cfg.items():
                    if "zhipu" in k.lower() and isinstance(v, str):
                        ZHIPU_API = v
                        break
            except (OSError, json.JSONDecodeError):
                pass


def rag_query(query, use_api=True):
    results = search(query, top_k=5)

    print(f"\n{'=' * 60}")
    print(f"Q: {query}")
    print(f"{'=' * 60}")

    if not results:
        print("\n未找到相关文档。")
        return

    print(f"\n检索到 {len(results)} 条相关文档：")
    for i, r in enumerate(results):
        score_pct = int(r["score"] * 100)
        bar = "#" * (score_pct // 5) + "." * max(0, 20 - score_pct // 5)
        label = f" [{r['label']}]" if r.get("label") else ""
        print(f"\n[{i + 1}] [{bar}] ({score_pct}%){label} {r['source']}")
        print(f"    {r['text'][:200]}...")

    if not use_api:
        return

    if not ZHIPU_API:
        print("\n未配置 ZHIPU_API_KEY，已完成本地检索，跳过 AI 生成。")
        return

    context = "\n\n---\n\n".join([f"【{r['source']}】\n{r['text']}" for r in results])
    prompt = f"""你是一名审计专家，请基于以下知识库内容回答用户问题。

知识库内容：
{context}

用户问题：{query}

请给出专业、准确的回答，并在引用时标注来源文件名。如果知识库内容不足以回答问题，请如实说明。"""

    import requests

    try:
        resp = requests.post(
            ZHIPU_URL,
            headers={"Authorization": f"Bearer {ZHIPU_API}", "Content-Type": "application/json"},
            json={
                "model": ZHIPU_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一名中国审计专家，精通政府审计、工程审计、财务审计。回答专业、简洁、准确。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            answer = resp.json()["choices"][0]["message"]["content"]
            print(f"\nAI 回答：\n{answer}")
        else:
            print(f"\nAPI error: {resp.status_code}")
    except Exception as e:
        print(f"\nAPI call failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rongce RAG query")
    parser.add_argument("query", nargs="*", help="审计问题")
    parser.add_argument("--no-api", action="store_true", help="只做本地检索，不调用外部模型")
    args = parser.parse_args()

    query = " ".join(args.query) if args.query else input("请输入审计问题：")
    rag_query(query, use_api=not args.no_api)
