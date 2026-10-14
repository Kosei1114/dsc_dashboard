# このファイルの役割：
#   各アプリを1つのURLの下で公開する入口です。
#   リポジトリのルートで `python app.py` を実行します。
#   各アプリの設定やデータ処理は、それぞれの apps/ 配下に置きます。

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

from apps.dashboard.app import app as dashboard_app
from apps.dashboard.config import PORT
from apps.hydroponics.app import app as hydroponics_app

# / はダッシュボード、それ以外の登録したパスは各アプリが担当します。
application = DispatcherMiddleware(
    dashboard_app, {"/apps/hydroponics": hydroponics_app}
)


if __name__ == "__main__":
    # 本番では `waitress-serve --host=0.0.0.0 --port=8000 app:application` を使います。
    run_simple("127.0.0.1", PORT, application, use_reloader=True, threaded=True)
