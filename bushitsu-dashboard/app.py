# このファイルの役割：
#   Flaskアプリの本体です。画面とAPIのURLを、このファイルにまとめて並べます。
#   開発中は、リポジトリのルートで `python app.py` を実行し、
#   ブラウザで http://127.0.0.1:8000/ を開きます。

import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template

import config

app = Flask(__name__)
# APIが返すJSONの日本語を "水" のような記号にせず、そのまま読める形で出す
app.json.ensure_ascii = False


def setup_logging():
    """logs/app.log にログを書き出す設定をする。"""
    config.LOG_DIR.mkdir(exist_ok=True)
    # ファイルが1MBを超えたら app.log.1 などに名前を変えて、新しいファイルに書き始める（3世代まで残す）
    handler = RotatingFileHandler(
        config.LOG_DIR / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)


setup_logging()


# ===== 画面 =====


@app.route("/")
def index():
    """ダッシュボードの画面。"""
    # ブラウザ側のJavaScript（static/dashboard.js）に渡す設定。
    # ブラウザから誰でも見られるので、秘密情報は絶対に入れないこと。
    js_config = {
        "timezone": config.TIMEZONE,
        "nightStart": config.NIGHT_START,
        "nightEnd": config.NIGHT_END,
        "panelRefreshSeconds": config.PANEL_REFRESH_SECONDS,
        "calendarRefreshSeconds": config.CALENDAR_REFRESH_SECONDS,
    }
    return render_template("index.html", panels=config.PANELS, js_config=js_config)


# ===== API（JSONを返すURL） =====
# パネルを追加するときは、ここに「@app.route("/api/panels/<パネルID>")」の関数を足します。


if __name__ == "__main__":
    # 開発用のサーバーで起動する（ラズパイの本番では waitress を使う）
    app.run(host="127.0.0.1", port=config.PORT, debug=True)
