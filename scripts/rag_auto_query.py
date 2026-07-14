#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG知识库自动查询 (RAG Auto Query) v1.0
=======================================
每天自动从RAG知识库抽取"值得关注"的内容，
推送给团队成员。

集成到engine.py作为知识管理员Agent的扩展任务。

用法:
  python rag_auto_query.py daily    # 每日精选推送
  python rag_auto_query.py search <query>  # 搜索并格式化输出
  python rag_auto_query.py stats    # 知识库统计
"""
import json, os, sys, random
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
TZ = timezone(timedelta(hours=8))
RAG_SERVER = "http://127.0.0.1:5000"
OUTPUT_DIR = ROOT / "knowledge" / "rag_daily"

def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def query_rag(query_text, top_k=5):
    """调用RAG知识库API查询"""
    try:
        import urllib.request
        import urllib.parse
        params = urllib.parse.urlencode({"q": query_text, "k": top_k, "source": "all"})
        url = f"{RAG_SERVER}/api/rag/query?{params}"
        resp = urllib.request.urlopen(url, timeout=10)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "results": []}

def query_deepseek(query_text):
    """调用智析RAG DeepSeek生成回答"""
    try:
        import urllib.request
        data = json.dumps({"query": query_text, "stream": False}).encode("utf-8")
        req = urllib.request.Request(
            f"{RAG_SERVER}/api/rag/query",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "answer": "RAG服务器暂不可用"}

# ── 精选每日话题 ──
DAILY_TOPICS = [
    "2026年最新审计政策法规变化",
    "审计报告常见错误和整改建议",
    "政府采购审计重点难点",
    "绩效评价指标体系设计要点",
    "经济责任审计最新规定",
    "专项资金审计常见问题",
    "工程审计中造价控制要点",
    "财政监督检查重点领域",
    "大数据审计方法最新进展",
    "预算执行审计关注重点",
]

def cmd_daily():
    """每日精选：从RAG抽取3条话题"""
    ensure_output_dir()
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    print(f"\n📚 RAG知识库每日精选 — {today}")
    print(f"{'='*55}")

    # 选择今天的话题（每周轮换）
    week = datetime.now(TZ).isocalendar()[1]
    day = datetime.now(TZ).weekday()
    topics = DAILY_TOPICS[(week * 3) % len(DAILY_TOPICS):][:3]
    if len(topics) < 3:
        topics = DAILY_TOPICS[:3]

    results = []
    for topic in topics:
        print(f"\n📖 查询: {topic}")
        resp = query_deepseek(topic)
        answer = resp.get("answer", resp.get("results", []))
        if isinstance(answer, list):
            answer = answer[0] if answer else "（无结果）"

        results.append({
            "topic": topic,
            "answer": answer[:500],
            "date": today,
        })
        print(f"  ✅ 获取完成 ({len(str(answer))} chars)")

    # 保存今日精选
    output = {
        "date": today,
        "topics": results,
        "source": "RAG知识库 (127.0.0.1:5000)",
    }
    output_path = OUTPUT_DIR / f"daily_{today}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*55}")
    print(f"✅ 今日精选已保存: {output_path}")
    print(f"话题数: {len(results)}")
    print(f"{'='*55}\n")

    # 输出Markdown版本
    md_path = OUTPUT_DIR / f"daily_{today}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# 📚 RAG知识库每日精选 — {today}\n\n")
        for r in results:
            f.write(f"## {r['topic']}\n\n")
            f.write(f"{r['answer']}\n\n")
            f.write("---\n\n")
    print(f"  Markdown: {md_path}")

def cmd_search(query):
    """搜索RAG"""
    print(f"\n🔍 RAG搜索: {query}")
    resp = query_deepseek(query)
    answer = resp.get("answer", resp.get("error", "无结果"))
    print(f"\n{answer[:1000]}")
    print("\n" + "=" * 40)

def cmd_stats():
    """知识库统计"""
    import subprocess
    try:
        result = subprocess.run(
            ["python", "-X", "utf8", "scripts/rag_query.py", "统计知识库"],
            capture_output=True, text=True, timeout=30,
            cwd=str(ROOT)
        )
        print(result.stdout[:2000] if result.stdout else result.stderr[:500])
    except Exception as e:
        print(f"RAG统计失败: {e}")
        print("尝试备用统计...")
        kb_path = ROOT / "knowledge"
        md_files = list(kb_path.rglob("*.md"))
        print(f"Markdown文件数: {len(md_files)}")

def main():
    import sys
    if len(sys.argv) < 2:
        print("用法: python rag_auto_query.py [daily|search <query>|stats]")
        return
    cmd = sys.argv[1]
    if cmd == "daily":
        cmd_daily()
    elif cmd == "search" and len(sys.argv) > 2:
        cmd_search(" ".join(sys.argv[2:]))
    elif cmd == "stats":
        cmd_stats()
    else:
        print("用法: python rag_auto_query.py [daily|search <query>|stats]")

if __name__ == "__main__":
    main()