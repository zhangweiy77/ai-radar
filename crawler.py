#!/usr/bin/env python3
"""AI 工具雷达 · 每日爬虫
抓取 GitHub 上最受关注的 AI 开源项目（总榜）与近 90 天冒头的新星，
写入 data/latest.json，并刷新 README 的榜单区（<!-- DATA_START --> ~ <!-- DATA_END -->）。
纯标准库，无第三方依赖；有 GITHUB_TOKEN 环境变量时自动使用（提高接口额度）。
"""
import json, os, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

API = "https://api.github.com/search/repositories"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def search(q, per_page):
    url = API + "?" + urllib.parse.urlencode(
        {"q": q, "sort": "stars", "order": "desc", "per_page": per_page})
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "zhangshuji-ai-radar"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["items"]

def slim(it):
    return {"name": it["full_name"], "url": it["html_url"],
            "desc": (it.get("description") or "").strip(),
            "stars": it["stargazers_count"],
            "lang": it.get("language") or "-",
            "created": it["created_at"][:10]}

def table(rows):
    out = ["| 项目 | ⭐ Stars | 语言 | 一句话简介 |", "|---|---:|---|---|"]
    for r in rows:
        d = (r["desc"] or "").replace("|", " ").replace("\n", " ")[:80]
        out.append(f"| [{r['name']}]({r['url']}) | {r['stars']:,} | {r['lang']} | {d} |")
    return "\n".join(out)

def main():
    since = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
    top = [slim(x) for x in search("AI OR LLM OR GPT in:name,description stars:>5000", 15)]
    rising = [slim(x) for x in search(
        f"AI OR LLM OR agent in:name,description created:>{since} stars:>800", 10)]
    data = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "top": top, "rising": rising}
    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    block = ("<!-- DATA_START -->\n"
             f"_数据更新于 {data['updated']}（爬虫自动抓取）_\n\n"
             "### 🏆 总榜 · 最受关注的 AI 开源项目\n\n" + table(top) +
             "\n\n### 🌱 新星榜 · 近 90 天冒头的新项目\n\n" + table(rising) +
             "\n<!-- DATA_END -->")
    readme = open("README.md", encoding="utf-8").read()
    s = readme.index("<!-- DATA_START -->")
    e = readme.index("<!-- DATA_END -->") + len("<!-- DATA_END -->")
    open("README.md", "w", encoding="utf-8").write(readme[:s] + block + readme[e:])
    print("updated:", data["updated"], "| top:", len(top), "| rising:", len(rising))

if __name__ == "__main__":
    main()
