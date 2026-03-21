#!/usr/bin/env python3
"""
ニュース収集エージェント - Claude Web Searchで会計・ERP関連ニュースを収集

使い方:
  python3 news_agent.py          # ニュース収集・分析・出力
  python3 news_agent.py --save   # 結果をファイルにも保存
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic

MODEL_SEARCH = "claude-sonnet-4-6"   # Web検索用（Haiku非対応のため）
MODEL_ANALYZE = "claude-haiku-4-5"  # 分析・整形用（コスト削減）
OUTPUT_FILE = Path(__file__).parent / "news_picks.json"

SYSTEM_PROMPT = """あなたはERPコンサルタント（会計担当）のX/noteコンテンツ戦略アドバイザーです。

【アカウント情報】
- X: @AccountingForSE（ITコンサル・SEのための会計）
- テーマ: 簿記では教えてくれない実務会計・ERP・経理のリアル
- ターゲット: ITコンサル・SE
- 目標: フォロワー300人達成・note収益向上
- note: note.com/accountingforse

ウェブ検索で収集した最新ニュースを、X投稿・noteコンテンツのネタとして整理してください。"""

SEARCH_QUERIES = [
    "会計 ERP 経理 DX 最新ニュース 2026",
    "不正会計 内部統制 インボイス 電子帳簿 2026",
]

OUTPUT_FORMAT = """
以下の形式で今日のニュースピックアップを出力してください：

## 📰 {date} 会計・ERPニュースピックアップ

各ネタ（3〜5件）について：
**[連番] 記事タイトル**
- 要約: 1〜2行
- X投稿案: （140字以内、ITコンサル・SEに刺さる切り口で）
- note展開: ◎/○/△ + 理由1行
- ターゲット: どんなSE/コンサルに刺さるか

---

## 🎯 今週の注目テーマ
（1〜2行でまとめ）
""".format(date=datetime.now().strftime('%Y-%m-%d'))


def collect_news(client: anthropic.Anthropic) -> str:
    """Step1: Sonnetでニュースを検索・収集（タイトルと要約のみ抽出）"""
    response = client.messages.create(
        model=MODEL_SEARCH,
        max_tokens=1000,  # 低く抑えてコスト削減
        system="あなたはニュース収集アシスタントです。",
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{"role": "user", "content": f"""以下のクエリで検索し、見つかった記事のタイトルとURL、1行要約をリスト形式で返してください。分析は不要です。

{chr(10).join(f'- {q}' for q in SEARCH_QUERIES)}"""}]
    )
    parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(parts)


def analyze_news(client: anthropic.Anthropic, raw_news: str) -> str:
    """Step2: Haikusで収集ニュースを分析・整形（コスト削減）"""
    response = client.messages.create(
        model=MODEL_ANALYZE,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"""以下のニュース一覧から、X投稿・noteコンテンツのネタになるものを選んで分析してください。

【収集ニュース】
{raw_news}

{OUTPUT_FORMAT}"""}]
    )
    return response.content[0].text


def collect_and_analyze(client: anthropic.Anthropic) -> str:
    """2段階でニュース収集・分析（Sonnet検索→Haiku分析）"""
    print("  Step1: ニュース検索中（Sonnet）...", flush=True)
    raw_news = collect_news(client)

    print("  Step2: 分析・整形中（Haiku）...", flush=True)
    return analyze_news(client, raw_news)


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: ANTHROPIC_API_KEY が設定されていません。")
        sys.exit(1)

    save_file = "--save" in sys.argv

    print(f"🔍 ニュース収集・分析中... ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")

    client = anthropic.Anthropic(api_key=api_key)
    result = collect_and_analyze(client)

    print(result)

    if save_file:
        entry = {
            "date": datetime.now().isoformat(),
            "analysis": result,
        }
        history = []
        if OUTPUT_FILE.exists():
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        history.append(entry)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"\n💾 保存: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
