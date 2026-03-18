"""
Google Drive へ日次投稿文テキストファイルをアップロードするスクリプト。

【初回セットアップ手順】
1. Google Cloud Console (https://console.cloud.google.com/) でプロジェクトを作成
2. Google Drive API を有効化
3. 「OAuth 2.0 クライアントID」を作成（アプリの種類: デスクトップアプリ）
4. credentials.json をこのスクリプトと同じ scripts/ ディレクトリに配置
5. pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
6. python upload_to_drive.py --setup で初回認証（ブラウザが開きます）

【通常実行】
  python upload_to_drive.py                   # 今日の日付のファイルをアップロード
  python upload_to_drive.py --date 2026-03-18 # 特定日付を指定
  python upload_to_drive.py --folder-id <ID>  # 保存先フォルダIDを指定
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
POSTS_DIR = REPO_ROOT / "posts" / "daily"
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent / "token.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print("エラー: credentials.json が見つかりません。")
                print(f"  配置先: {CREDENTIALS_FILE}")
                print("  Google Cloud Console で OAuth2 クライアントIDを作成してください。")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print("認証完了。token.json を保存しました。")

    return creds


def upload_file(date_str: str, folder_id: str | None = None):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    # 対象ファイルのパスを決定
    md_path = POSTS_DIR / f"{date_str}.md"
    txt_path = POSTS_DIR / f"{date_str}.txt"

    if md_path.exists():
        source_path = md_path
        drive_filename = f"投稿文案_{date_str}.txt"
        mime_type = "text/plain"
    elif txt_path.exists():
        source_path = txt_path
        drive_filename = f"投稿文案_{date_str}.txt"
        mime_type = "text/plain"
    else:
        print(f"エラー: {POSTS_DIR}/{date_str}.md が見つかりません。")
        sys.exit(1)

    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)

    # 既存ファイルを検索して上書き or 新規作成
    query = f"name='{drive_filename}' and trashed=false"
    if folder_id:
        query += f" and '{folder_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    existing = results.get("files", [])

    media = MediaFileUpload(str(source_path), mimetype=mime_type)
    file_metadata = {"name": drive_filename}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    if existing:
        # 上書き更新
        file_id = existing[0]["id"]
        service.files().update(
            fileId=file_id,
            body={"name": drive_filename},
            media_body=media,
        ).execute()
        print(f"更新完了: {drive_filename} (ID: {file_id})")
    else:
        # 新規作成
        result = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()
        print(f"アップロード完了: {drive_filename} (ID: {result['id']})")

    print(f"Google Drive 上のファイル名: {drive_filename}")


def main():
    parser = argparse.ArgumentParser(description="Google Drive へ投稿文をアップロード")
    parser.add_argument(
        "--date",
        default=datetime.today().strftime("%Y-%m-%d"),
        help="対象日付 (例: 2026-03-18)。省略時は今日の日付。",
    )
    parser.add_argument(
        "--folder-id",
        default=os.environ.get("GDRIVE_FOLDER_ID"),
        help="保存先フォルダのID (省略時: マイドライブ直下 or 環境変数 GDRIVE_FOLDER_ID)",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="初回認証のみ実行（ファイルはアップロードしない）",
    )
    args = parser.parse_args()

    try:
        import googleapiclient  # noqa: F401
    except ImportError:
        print("必要なライブラリがインストールされていません。以下を実行してください：")
        print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        sys.exit(1)

    if args.setup:
        get_credentials()
        print("セットアップ完了。次回から --setup なしで実行できます。")
        return

    upload_file(args.date, args.folder_id)


if __name__ == "__main__":
    main()
