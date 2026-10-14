# このファイルの役割：ルートからダッシュボードを起動する入口です。
# 今後、各アプリのURLをここで振り分けます。
from apps.dashboard.app import app as application
from apps.dashboard.config import PORT


if __name__ == "__main__":
    application.run(host="127.0.0.1", port=PORT, debug=True)
