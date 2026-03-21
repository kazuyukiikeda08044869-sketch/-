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

MODEL = "claude-sonnet-4-6"
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


def collect_and_analyze(client: anthropic.Anthropic) -> str:
    """Web検索でニュース収集し分析する"""

    search_prompt = f"""以下の検索クエリで最新の会計・ERP関連ニュースを検索してください：

{chr(10).join(f'- {q}' for q in SEARCH_QUERIES)}

検索で見つかった記事をもとに、X投稿・noteコンテンツのネタになるものを選んで整理してください。

{OUTPUT_FORMAT}"""

    # Web検索ツールを使ってニュース収集
    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{"role": "user", "content": search_prompt}]
    )

    # テキストブロックを結合して返す
    result_parts = []
    for block in response.content:
        if block.type == "text":
            result_parts.append(block.text)

    return "\n".join(result_parts) if result_parts else "ニュースの取得に失敗しました。"


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
