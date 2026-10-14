# 部室アプリ

部室ダッシュボードと、そこから開く各アプリを同じリポジトリで管理します。
Python 3.11以上を使い、画面はHTML・CSS・素のJavaScriptで作ります。

## 構成

```text
dsc_dashboard/
├── app.py                  # 各Webアプリを共通のURLで公開する入口
├── requirements.txt        # 各アプリの依存ライブラリをまとめて入れる
├── pytest.ini              # 全体のテスト設定
├── apps/
│   ├── dashboard/          # カレンダー、時計、各アプリの要約パネル
│   └── hydroponics/        # 水耕栽培の専用画面、要約API、センサー処理
├── tests/                  # アプリ同士の接続のテスト
├── 部室ダッシュボード 仕様書.md
└── 水耕栽培センサー管理 技術仕様書.md
```

各アプリは自分の `config.py`・`.env`・テンプレート・依存ライブラリを持ちます。
ダッシュボードは水耕栽培の内部処理やDBを直接読みません。

## 起動

以下のコマンドはすべて、リポジトリのルートで実行します。

Mac / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp apps/dashboard/.env.example apps/dashboard/.env
python app.py
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item apps/dashboard/.env.example apps/dashboard/.env
python app.py
```

Notionの設定は `apps/dashboard/.env` に書きます。
詳しくは [ダッシュボードのREADME](apps/dashboard/README.md) を見てください。
Notionが未設定でも、両方のアプリを開けます。

| URL | 内容 |
| --- | --- |
| `http://127.0.0.1:8000/` | ダッシュボード |
| `http://127.0.0.1:8000/apps/hydroponics/` | 水耕栽培アプリ |
| `http://127.0.0.1:8000/apps/hydroponics/api/summary` | 水耕栽培の要約JSON |

ダッシュボードの水耕栽培パネルを押すと、同じタブで専用画面を開きます。
専用画面の「ダッシュボードに戻る」で戻れます。
ダッシュボードから開いた場合は、3分間操作がなければ自動で戻ります。
水耕栽培アプリを直接開いた場合は、自動で戻りません。

### アプリだけを起動する

```bash
python -m apps.dashboard.app    # ダッシュボードだけ（ポート8000）
python -m apps.hydroponics.app  # 水耕栽培だけ（ポート8001）
```

単体起動した水耕栽培アプリは `http://127.0.0.1:8001/` で開きます。
ダッシュボード単体の起動では `/apps/hydroponics/` は提供されません。
両方を連携させるときはルートの `python app.py` を使ってください。

### ラズパイでの本番起動

```bash
waitress-serve --host=0.0.0.0 --port=8000 app:application
```

共通の入口は、[Flaskのアプリ振り分け](https://flask.palletsprojects.com/en/stable/patterns/appdispatch/)を使います。
1つのWebサーバー内で、URLごとに独立したFlaskアプリへ振り分けます。
ブラウザからは同じサイトなので、iPadでもPCでも同じURLでAPIと専用画面を開けます。
将来プロセスを分ける場合も、HTTPサーバー側で同じパスに振り分ければ各アプリのURLを維持できます。

## 現在の実装範囲

- ダッシュボードの時計・夜間表示・Notionカレンダー。
- 水耕栽培の要約パネル、専用画面への遷移、戻る操作。
- 両画面が共用する要約APIと表示部品。1分ごとに取得し、失敗時は前回の表示を残す。
- センサー3種類の `read()` のひな形。

水耕栽培の収集・DB・判定・通知・グラフは未実装です。
現在の要約APIは「未計測」を返します。実データに接続する際は
`apps/hydroponics/summary.py` の `get_summary()` を実装してください。
ダッシュボード側のデータ取得処理を変更する必要はありません。

## アプリを追加する

1. `apps/<アプリ名>/` に専用画面と要約APIを作る。
2. ルートの `app.py` に `/apps/<アプリ名>` の振り分けを追加する。
3. `apps/dashboard/templates/panels/<パネルID>.html` に表示関数を登録する。
4. `apps/dashboard/config.py` の `PANELS` に `api_url` と `detail_url` を登録する。
5. 必要な場合は、ルートの `requirements.txt` にそのアプリの依存ライブラリを追加する。

APIや表示部品のURLは `/apps/<アプリ名>/...` を使います。
専用画面内のURLはFlaskの `url_for()` で作ると、単体起動と共通入口の両方に対応できます。
ダッシュボード内だけで使う小さなパネルは、従来の `/api/panels/<パネルID>` も利用できます。

## 確認

```bash
pytest
node tests/test_frontend.cjs
```

Pythonのテストは両アプリとURLの接続、Notionカレンダーを確認します。
JavaScriptのテストはNode.jsの標準機能を使い、要約の描画・更新失敗・自動復帰を確認します。
