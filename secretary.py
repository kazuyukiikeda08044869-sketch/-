#!/usr/bin/env python3
"""
Secretary Agent - X運用戦略の記憶・補完・要約エージェント

使い方:
  python3 secretary.py "メモしたい内容"     # 記憶 + 補完
  python3 secretary.py --summary            # 要約
  python3 secretary.py --list               # 記憶一覧
  python3 secretary.py --reset              # 記憶リセット
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic

# --- 設定 ---
MEMORY_FILE = Path(__file__).parent / "secretary_memory.json"
MODEL = "claude-opus-4-6"

SECRETARY_CONTEXT = """
あなたは優秀な秘書エージェントです。以下のユーザー情報を常に念頭に置いてください。

【ユーザープロフィール】
- 職種: ERPコンサルタント（会計担当）
- Xアカウント: @AccountingForSE（ITコンサル・SEのための会計）
- 運用開始: 2026年3月（約3週間）
- 現状: フォロワー67人 → 目標300人
- 最終目的: note収益の向上

【Xアカウントの軸】
- テーマ: 簿記では教えてくれない実務会計・ERP・経理のリアル
- ターゲット: ITコンサル・SE
- note: note.com/accountingforse

【運用ルール】
- 顔出しなし
- 所属企業・クライアント名は非公開
- ニュースで話題の企業名は使用OK

【秘書の役割】
1. ユーザーが話した内容を記憶・蓄積する
2. 話した内容に対して補完・深掘りを行う
3. 「要約して」と指示されたとき、記憶した内容を整理して出力する

記憶・補完・要約の際は常にXフォロワー300人達成・note収益向上という目標を意識してください。
"""


def load_memory() -> dict:
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"entries": [], "created_at": datetime.now().isoformat()}


def save_memory(memory: dict):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def add_memory_entry(memory: dict, user_input: str, secretary_response: str):
    memory["entries"].append({
        "timestamp": datetime.now().isoformat(),
        "user": user_input,
        "secretary": secretary_response,
    })
    save_memory(memory)


def build_memory_text(memory: dict) -> str:
    if not memory["entries"]:
        return "（まだ記憶はありません）"
    lines = []
    for i, entry in enumerate(memory["entries"], 1):
        ts = entry["timestamp"][:16].replace("T", " ")
        lines.append(f"[{i}] {ts}\n　USER: {entry['user']}\n　SECRETARY: {entry['secretary']}")
    return "\n\n".join(lines)


def process_input(client: anthropic.Anthropic, memory: dict, user_input: str) -> str:
    memory_text = build_memory_text(memory)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SECRETARY_CONTEXT,
        messages=[{
            "role": "user",
            "content": f"""【これまでの記憶】
{memory_text}

【今回のユーザー入力】
{user_input}

---
上記のユーザー入力を受けて、以下を行ってください：
1. 内容を受け取り、理解したことを簡潔に確認する
2. X運用・note収益向上の観点から、内容を補完・深掘りする
3. 次のアクションや考えるべき点があれば提案する

簡潔かつ実用的に応答してください。"""
        }]
    )
    reply = response.content[0].text
    add_memory_entry(memory, user_input, reply)
    return reply


def summarize_memory(client: anthropic.Anthropic, memory: dict) -> str:
    if not memory["entries"]:
        return "まだ記憶した内容がありません。"
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SECRETARY_CONTEXT,
        messages=[{
            "role": "user",
            "content": f"""【記憶した内容】
{build_memory_text(memory)}

---
以下の形式で要約・整理してください：

1. **主なアイデア・思考のまとめ**（箇条書き）
2. **X運用への示唆**（具体的な投稿ネタ・戦略案）
3. **noteコンテンツへの示唆**
4. **次に考えるべきこと・アクション候補**"""
        }]
    )
    return f"【記憶の要約】\n\n{response.content[0].text}"


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: ANTHROPIC_API_KEY が設定されていません。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    memory = load_memory()
    args = sys.argv[1:]

    if not args:
        print("使い方: python3 secretary.py \"メモ内容\"")
        print("        python3 secretary.py --summary")
        print("        python3 secretary.py --list")
        print("        python3 secretary.py --reset")
        print(f"\n現在の記憶数: {len(memory['entries'])}件")
        sys.exit(0)

    if args[0] == "--summary":
        print(summarize_memory(client, memory))

    elif args[0] == "--list":
        print(f"【記憶一覧】({len(memory['entries'])}件)\n")
        print(build_memory_text(memory))

    elif args[0] == "--reset":
        if MEMORY_FILE.exists():
            MEMORY_FILE.unlink()
        print("記憶をリセットしました。")

    else:
        user_input = " ".join(args)
        print(process_input(client, memory, user_input))


if __name__ == "__main__":
    main()
