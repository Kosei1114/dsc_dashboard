# このファイルの役割：
#   水耕栽培アプリ専用の設定を置きます。ダッシュボードの設定は読みません。

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 単体起動時に「ダッシュボードに戻る」リンクを出したい場合のURL。
# 共通の入口（ルートの app.py）で動かす場合は空のままでよいです。
DASHBOARD_URL = os.getenv("HYDRO_DASHBOARD_URL", "")
PORT = int(os.getenv("HYDRO_PORT", "8001"))
SUMMARY_REFRESH_SECONDS = 60
FETCH_TIMEOUT_SECONDS = 10
IDLE_RETURN_SECONDS = 180
