# このファイルの役割：
#   Flaskアプリの本体です。画面とAPIのURLを、このファイルにまとめて並べます。
#   開発中は、リポジトリのルートで `python app.py` を実行し、
#   ブラウザで http://127.0.0.1:8000/ を開きます。

import logging
from datetime import date
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, render_template, request

import config
import notion_calendar

app = Flask(__name__)
# APIが返すJSONの日本語を "\u6c34" のような記号にせず、そのまま読める形で出す
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
        "calendarOpenUrl": config.NOTION_CALENDAR_OPEN_URL,
    }
    return render_template(
        "index.html",
        panels=config.PANELS,
        js_config=js_config,
        notion_configured=notion_calendar.is_configured(),
    )


# ===== API（JSONを返すURL） =====
# パネルを追加するときは、ここに「@app.route("/api/panels/<パネルID>")」の関数を足します。


@app.route("/api/calendar")
def api_calendar():
    """カレンダーの予定。/api/calendar?start=2026-09-27&end=2026-11-08 のように表示期間を指定する。"""
    # Notionの設定がまだなければ、予定なしとして返す（画面には「未設定」の案内が出る）
    if not notion_calendar.is_configured():
        return jsonify([])

    try:
        # "2026-09-27T00:00:00+09:00" のような形で渡されても動くよう、先頭の日付部分（10文字）だけを使う
        range_start = date.fromisoformat(request.args["start"][:10])
        range_end = date.fromisoformat(request.args["end"][:10])
    except (KeyError, ValueError):
        return jsonify({"error": "start と end を YYYY-MM-DD の形で指定してください"}), 400

    try:
        events = notion_calendar.get_events(range_start, range_end)
    except Exception:
        # 詳しいエラーの内容は notion_calendar.py が logs/app.log に書いている
        return jsonify({"error": "Notionから予定を取得できませんでした"}), 502
    return jsonify(events)


if __name__ == "__main__":
    # 開発用のサーバーで起動する（ラズパイの本番では waitress を使う）
    app.run(host="127.0.0.1", port=config.PORT, debug=True)
