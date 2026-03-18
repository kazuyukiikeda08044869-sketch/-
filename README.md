# 会計×X投稿 提案システム

**テーマ：「簿記では教えてくれない」**

会計実務・ERP導入・会計システム導入に関するX投稿案を定期的に提案するリポジトリです。

## ディレクトリ構成

```
posts/
  daily/        # 日次投稿案（YYYY-MM-DD.md） ← メイン
  weekly/       # 週次投稿案（曜日別）
  news-hooks/   # ニュース連動投稿テンプレート
  threads/      # スレッド形式の投稿案
scripts/
  upload_to_drive.py  # Google Drive アップロードスクリプト
strategy/
  algorithm.md  # Xアルゴリズム攻略メモ
  kpi.md        # インプレッション・エンゲージメント指標
```

## 投稿頻度の目安

- **毎日**：3投稿/日（直近ニュース連動）
- **ニュース連動**：X リポスト数・Web 掲載数が多いものを3件選定

## 更新ルール

`posts/daily/YYYY-MM-DD.md` を毎日生成する。
生成後、`scripts/upload_to_drive.py` で Google Drive へ自動保存。

---

## Google Drive 連携セットアップ

### 1. 必要ライブラリのインストール

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 2. GCP で OAuth2 認証情報を作成

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成
2. **Google Drive API** を有効化
3. 「認証情報」→「OAuth 2.0 クライアントID」作成（種類: デスクトップアプリ）
4. ダウンロードした JSON を `scripts/credentials.json` として保存

### 3. 初回認証

```bash
python scripts/upload_to_drive.py --setup
```

ブラウザが開くので Google アカウントでログイン → `scripts/token.json` が生成される。

### 4. 日次アップロード

```bash
# 今日分を Drive にアップロード（ファイル名: 投稿文案_YYYY-MM-DD.txt）
python scripts/upload_to_drive.py

# 特定日を指定
python scripts/upload_to_drive.py --date 2026-03-18

# 保存先フォルダを指定（Drive の共有フォルダID）
python scripts/upload_to_drive.py --folder-id <FOLDER_ID>
# または環境変数で指定
export GDRIVE_FOLDER_ID=<FOLDER_ID>
```

### フォルダIDの確認方法

Google Drive でフォルダを開き、URL の末尾を確認：
`https://drive.google.com/drive/folders/` **← ここがフォルダID**
