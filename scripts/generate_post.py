"""
X投稿文を posts/daily/YYYY-MM-DD.md に保存するスクリプト。

使い方：
  python scripts/generate_post.py
  python scripts/generate_post.py --date 2026-03-19
  python scripts/generate_post.py --append   # 既存ファイルに追記

Claudeが投稿文を生成した後、このスクリプトで保存する。
または標準入力から受け取ることも可能：

  echo "投稿文テキスト" | python scripts/generate_post.py --stdin
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
POSTS_DIR = REPO_ROOT / "posts" / "daily"


def get_date_str(date_arg: str | None) -> str:
    if date_arg:
        return date_arg
    return datetime.today().strftime("%Y-%m-%d")


def save_post(date_str: str, content: str, append: bool = False) -> Path:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    path = POSTS_DIR / f"{date_str}.md"

    if append and path.exists():
        existing = path.read_text(encoding="utf-8")
        separator = "\n\n---\n\n"
        path.write_text(existing + separator + content, encoding="utf-8")
    else:
        if path.exists():
            print(f"警告: {path} は既に存在します。上書きします。")
        path.write_text(content, encoding="utf-8")

    return path


def build_header(date_str: str) -> str:
    return f"# 投稿文案（ニュース連動）{date_str}\n\n"


def main():
    parser = argparse.ArgumentParser(description="X投稿文を日次ファイルに保存する")
    parser.add_argument("--date", help="対象日付 YYYY-MM-DD（省略時は今日）")
    parser.add_argument("--append", action="store_true", help="既存ファイルに追記する")
    parser.add_argument("--stdin", action="store_true", help="標準入力からコンテンツを受け取る")
    args = parser.parse_args()

    date_str = get_date_str(args.date)

    if args.stdin:
        content = sys.stdin.read()
    else:
        print(f"投稿文を入力してください（Ctrl+D で終了）：")
        content = sys.stdin.read()

    path = POSTS_DIR / f"{date_str}.md"
    if not args.append and not path.exists():
        content = build_header(date_str) + content

    saved_path = save_post(date_str, content, append=args.append)
    print(f"保存完了: {saved_path}")


if __name__ == "__main__":
    main()
