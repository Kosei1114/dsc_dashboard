# このファイルの役割：
#   ダッシュボードの設定値をまとめて置く場所です。
#   - 秘密情報や環境ごとに違う値は .env に書き、ここで読み込みます。
#   - それ以外の設定は、このファイルに直接書きます。
#   設定を変えたら、サーバーを再起動してください。

import os
from pathlib import Path

from dotenv import load_dotenv

# このアプリのフォルダ（apps/dashboard）
BASE_DIR = Path(__file__).resolve().parent

# .env の中身を環境変数として読み込む（.env がなくてもエラーにはならない）
load_dotenv(BASE_DIR / ".env")


# ===== .env から読む値（秘密情報・環境ごとに違う値） =====
# 書き方は .env.example を見てください。.env に書いていない値は空文字 "" になります。

# Notion連携（インテグレーション）のトークン。ブラウザやログには絶対に出さないこと
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
# カレンダーのデータベースID
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
# カレンダーをタップしたときに開くURL（https://〜 でも notion://〜 でもよい）
NOTION_CALENDAR_OPEN_URL = os.getenv("NOTION_CALENDAR_OPEN_URL", "")


# ===== 画面 =====

# 右側の3つの枠に表示するパネル（上から枠1・枠2・枠3）。
# None の枠は「準備中」と表示されます。
# パネルの追加方法は README の「パネルの追加方法」を見てください。
PANELS = [
    # 水耕栽培パネルができたら、下の行の先頭の「# 」を消して、次の行の None を消す
    # {"id": "hydroponics", "title": "水耕栽培", "detail_url": "/panels/hydroponics"},
    None,  # 準備中
    None,  # 準備中
    None,  # 準備中
]

# 夜間表示（黒い背景に時計だけ）にする時間帯。"HH:MM" の形で書く。
# 開始が終了より遅い場合（22:00〜07:00など）は、日をまたぐ時間帯として扱います。
NIGHT_START = "22:00"
NIGHT_END = "07:00"

# パネルのデータを取り直す間隔（秒）
PANEL_REFRESH_SECONDS = 60

# カレンダーの予定を取り直す間隔（秒）
CALENDAR_REFRESH_SECONDS = 600

# 時計やカレンダーで使うタイムゾーン
TIMEZONE = "Asia/Tokyo"


# ===== Notionカレンダー =====

# 予定のタイトルが入っているプロパティの名前（Notionのデータベースの列名）
NOTION_TITLE_PROPERTY = "名前"

# 予定の日付が入っているプロパティの名前
NOTION_DATE_PROPERTY = "日付"

# サーバーがNotionの結果を使い回す時間（秒）。この間はNotionに問い合わせない
CALENDAR_CACHE_SECONDS = 300

# Notionで予定を探すとき、表示期間の前後に何日ぶん広げて探すか。
# 例: 31 なら、表示期間の31日前に始まった予定や、31日後まで続く予定も、表示期間にかかっていれば表示される。
# これより長い期間にわたる予定を表示したいときは、数を大きくする。
NOTION_LOOKBACK_DAYS = 31


# ===== サーバー =====

# Webサーバーが待ち受けるポート番号
PORT = 8000

# ログファイルを置くフォルダ
LOG_DIR = BASE_DIR / "logs"
