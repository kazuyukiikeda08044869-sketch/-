"""
日次投稿文をメールで送信するスクリプト。

【設定手順】
1. 下の CONFIG の FROM_ADDRESS / TO_ADDRESS / APP_PASSWORD を書き換える
2. python scripts/send_daily_post.py で送信

【Gmail アプリパスワードの取得方法】
1. Google アカウント → セキュリティ → 2段階認証プロセス（有効にする）
2. セキュリティ → 「アプリパスワード」で検索
3. アプリ名に任意の名前を入力（例: 投稿文送信）→「作成」
4. 表示された16桁のコードを APP_PASSWORD に貼り付ける
"""

import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ============================================================
# ここを書き換えてください
# ============================================================
CONFIG = {
    "FROM_ADDRESS": "your-gmail@gmail.com",   # 送信元 Gmail アドレス
    "TO_ADDRESS":   "your-phone@example.com", # 送信先（スマホで受け取るアドレス）
    "APP_PASSWORD":  "xxxx xxxx xxxx xxxx",   # Gmail アプリパスワード（16桁）
}
# ============================================================

REPO_ROOT = Path(__file__).parent.parent
POSTS_DIR = REPO_ROOT / "posts" / "daily"


def load_post(date_str: str) -> str:
    path = POSTS_DIR / f"{date_str}.md"
    if not path.exists():
        print(f"エラー: {path} が見つかりません。")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def build_body(date_str: str, content: str) -> str:
    """Markdown を読みやすいプレーンテキストに変換"""
    lines = []
    for line in content.splitlines():
        # コードブロックのバッククォートを除去
        if line.strip() in ("```", "```text"):
            continue
        # Markdown 見出しを整形
        if line.startswith("## "):
            lines.append("\n" + "=" * 40)
            lines.append(line.replace("## ", "").strip())
            lines.append("=" * 40)
        elif line.startswith("# "):
            continue  # タイトル行は省略
        else:
            lines.append(line)
    return "\n".join(lines)


def send_mail(date_str: str):
    content = load_post(date_str)
    body = build_body(date_str, content)

    msg = MIMEMultipart()
    msg["From"] = CONFIG["FROM_ADDRESS"]
    msg["To"] = CONFIG["TO_ADDRESS"]
    msg["Subject"] = f"【投稿文案】{date_str}"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(CONFIG["FROM_ADDRESS"], CONFIG["APP_PASSWORD"].replace(" ", ""))
        smtp.send_message(msg)

    print(f"送信完了: {CONFIG['TO_ADDRESS']} 宛に {date_str} 分を送信しました。")


if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.today().strftime("%Y-%m-%d")
    send_mail(date_str)
