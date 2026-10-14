# このファイルの役割：
#   水耕栽培の専用画面と、ダッシュボード向けの要約APIを提供します。
#   単体で動かすときは、ルートで `python -m apps.hydroponics.app` を実行します。

from flask import Flask, jsonify, render_template, request, url_for

from . import config, summary

app = Flask(__name__)
app.json.ensure_ascii = False


@app.route("/")
def index():
    """水耕栽培アプリの画面。ダッシュボードとは別のテンプレートを使う。"""
    # 共通の入口から開いた場合は同じサイトの / に戻れます。
    # 単体起動では、戻り先を .env に設定したときだけリンクを出します。
    dashboard_url = config.DASHBOARD_URL or ("/" if request.script_root else None)
    js_config = {
        "summaryUrl": url_for("api_summary"),
        "refreshSeconds": config.SUMMARY_REFRESH_SECONDS,
        "fetchTimeoutSeconds": config.FETCH_TIMEOUT_SECONDS,
        "dashboardUrl": dashboard_url,
        "idleReturnSeconds": (
            config.IDLE_RETURN_SECONDS
            if dashboard_url and request.args.get("from") == "dashboard"
            else 0
        ),
    }
    return render_template(
        "index.html", dashboard_url=dashboard_url, js_config=js_config
    )


@app.route("/api/summary")
def api_summary():
    """専用画面とダッシュボードが同じ要約データを使うための接続口。"""
    try:
        return jsonify(summary.get_summary())
    except Exception:
        app.logger.exception("水耕栽培の表示用データを取得できませんでした")
        return jsonify({"error": "水耕栽培のデータを取得できませんでした"}), 503


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=config.PORT, debug=True)
