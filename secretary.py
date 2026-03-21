#!/usr/bin/env python3
"""
Secretary Agent - X運用戦略の記憶・補完・要約エージェント
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

# 秘書のコンテキスト（あなたのプロフィール）
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
    """記憶ファイルを読み込む"""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"entries": [], "created_at": datetime.now().isoformat()}


def save_memory(memory: dict):
    """記憶をファイルに保存する"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def add_memory_entry(memory: dict, user_input: str, secretary_response: str):
    """記憶エントリを追加する"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user_input,
        "secretary": secretary_response,
    }
    memory["entries"].append(entry)
    save_memory(memory)


def build_memory_summary_text(memory: dict) -> str:
    """記憶内容をテキストにまとめる"""
    if not memory["entries"]:
        return "（まだ記憶はありません）"
    lines = []
    for i, entry in enumerate(memory["entries"], 1):
        ts = entry["timestamp"][:16].replace("T", " ")
        lines.append(f"[{i}] {ts}\n　USER: {entry['user']}\n　SECRETARY: {entry['secretary']}")
    return "\n\n".join(lines)


def process_input(client: anthropic.Anthropic, memory: dict, user_input: str) -> str:
    """ユーザー入力を処理して秘書の応答を返す"""

    # コマンド判定
    lower_input = user_input.strip().lower()

    # 要約コマンド
    if any(kw in lower_input for kw in ["要約", "まとめ", "サマリー", "summary"]):
        return summarize_memory(client, memory)

    # 記憶一覧コマンド
    if any(kw in lower_input for kw in ["記憶を見せて", "記憶一覧", "これまでの記憶"]):
        return f"【記憶一覧】\n\n{build_memory_summary_text(memory)}"

    # 通常入力: 記憶 + 補完
    memory_text = build_memory_summary_text(memory)

    messages = [
        {
            "role": "user",
            "content": f"""【これまでの記憶】
{memory_text}

【今回のユーザー入力】
{user_input}

---
上記のユーザー入力を受けて、以下を行ってください：
1. 内容を受け取り、理解したことを簡潔に確認する
2. X運用・note収益向上の観点から、内容を補完・深掘りする（具体的なアイデアや観点を追加）
3. 次のアクションや考えるべき点があれば提案する

簡潔かつ実用的に応答してください。""",
        }
    ]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SECRETARY_CONTEXT,
        messages=messages,
    )

    reply = response.content[0].text
    add_memory_entry(memory, user_input, reply)
    return reply


def summarize_memory(client: anthropic.Anthropic, memory: dict) -> str:
    """記憶した内容を要約する"""
    if not memory["entries"]:
        return "まだ記憶した内容がありません。"

    memory_text = build_memory_summary_text(memory)

    messages = [
        {
            "role": "user",
            "content": f"""【記憶した内容】
{memory_text}

---
上記の記憶内容を以下の形式で要約・整理してください：

1. **主なアイデア・思考のまとめ**（箇条書き）
2. **X運用への示唆**（具体的な投稿ネタ・戦略案）
3. **noteコンテンツへの示唆**
4. **次に考えるべきこと・アクション候補**

X目標（フォロワー300人・note収益向上）に向けた観点で整理してください。""",
        }
    ]

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SECRETARY_CONTEXT,
        messages=messages,
    )

    return f"【記憶の要約】\n\n{response.content[0].text}"


def clear_memory():
    """記憶をリセットする"""
    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()
    print("記憶をリセットしました。")


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: ANTHROPIC_API_KEY が設定されていません。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    memory = load_memory()

    print("=" * 50)
    print("秘書エージェント起動中")
    print("=" * 50)
    print("コマンド:")
    print("  通常入力  → 記憶 + 補完")
    print("  「要約して」→ 記憶の要約を出力")
    print("  「記憶を見せて」→ 記憶一覧を表示")
    print("  「リセット」→ 記憶を消去")
    print("  「終了」「quit」「exit」→ 終了")
    print("=" * 50)
    print(f"現在の記憶数: {len(memory['entries'])}件\n")

    while True:
        try:
            user_input = input("あなた: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            break

        if not user_input:
            continue

        if user_input in ["終了", "quit", "exit", "q"]:
            print("終了します。")
            break

        if user_input in ["リセット", "reset"]:
            clear_memory()
            memory = load_memory()
            continue

        print("\n秘書: ", end="", flush=True)
        try:
            response = process_input(client, memory, user_input)
            print(response)
        except anthropic.APIError as e:
            print(f"APIエラー: {e}")
        print()


if __name__ == "__main__":
    main()
