# このファイルの役割：
#   ダッシュボードの設定値をまとめて置く場所です。
#   - 秘密情報や環境ごとに違う値は .env に書き、ここで読み込みます。
#   - それ以外の設定は、このファイルに直接書きます。
#   設定を変えたら、サーバーを再起動してください。

from pathlib import Path

from dotenv import load_dotenv

# このファイルがあるフォルダ（リポジトリのルート）
BASE_DIR = Path(__file__).resolve().parent

# .env の中身を環境変数として読み込む（.env がなくてもエラーにはならない）
load_dotenv(BASE_DIR / ".env")


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


# ===== サーバー =====

# Webサーバーが待ち受けるポート番号
PORT = 8000

# ログファイルを置くフォルダ
LOG_DIR = BASE_DIR / "logs"
