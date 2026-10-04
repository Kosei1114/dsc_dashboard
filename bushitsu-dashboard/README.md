# 部室ダッシュボード

岡山大学DS部の部室に置いたiPadに常時表示する、Webのダッシュボードです。
画面の左半分にNotionのカレンダー、右半分に時計と機能ごとの「パネル」を並べます。

仕様はリポジトリのルートにある `部室ダッシュボード 仕様書.md` を見てください。

## いまできていること

| ステップ | 内容 | 状態 |
| --- | --- | --- |
| 1. 土台 | 左右分割の画面、時計、「準備中」の枠、夜間表示、スマホ向けの縦並び | 完了 |
| 2. カレンダー | Notionの予定を月表示、タップでNotionを開く | 完了 |
| 3. 水耕栽培 | センサー値の収集とパネル表示 | 未実装 |
| 4. ラズパイへの設置 | systemd・cron の設定 | 未実装 |
| 5. 外部公開 | Cloudflare Tunnel と Access | 未実装 |

## フォルダの中身

```text
bushitsu-dashboard/
├── README.md          # このファイル
├── requirements.txt   # 使うPythonライブラリの一覧
├── pytest.ini         # テストの設定
├── config.py          # 設定値（パネルの並び、夜間の時間帯など）
├── .env.example       # .env（秘密情報）の見本
├── app.py             # Flaskアプリ。画面とAPIのURLをここに並べる
├── notion_calendar.py # Notionから予定を取得し、FullCalendarの形に変換
├── panels/            # パネルごとの「APIが返すデータを作る」Pythonファイル
├── templates/         # 画面のHTML（Jinja2テンプレート）
│   ├── base.html      # 全画面に共通する骨組み
│   ├── index.html     # ダッシュボード
│   └── panels/        # パネルの中身のHTML（empty.html は「準備中」の枠）
├── static/
│   ├── style.css      # 見た目（色、文字の大きさ、配置）
│   ├── dashboard.js   # 時計、夜間表示、パネルの定期更新
│   └── calendar.js    # 左側のカレンダー（FullCalendar）
├── tests/             # pytest のテスト
└── logs/              # ログ（Git管理外。起動すると自動で作られる）
```

仕様書の構成から1つだけファイルを増やしています。カレンダーの処理は `static/dashboard.js` に入れず、
`static/calendar.js` に分けました。「カレンダーを直したいときはこのファイル」と分かりやすくするためです。

## 1. 自分のPCで起動する

Python 3.11 以上が必要です。ターミナル（Windowsは「PowerShell」）を開き、
このフォルダ（`bushitsu-dashboard`）に移動してから、次のコマンドを順に実行します。

### 仮想環境を作ってライブラリを入れる（最初の1回だけ）

Mac / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> PowerShell で「スクリプトの実行が無効」と出たら、
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` を一度実行してからやり直してください。

### .env を作る（最初の1回だけ）

`.env.example` をコピーして `.env` という名前のファイルを作ります。

```bash
cp .env.example .env        # Mac / Linux
copy .env.example .env      # Windows
```

中身はあとで「2. Notion連携の準備」で書きます。空のままでも起動でき、
そのときはカレンダーの下に「Notionが未設定です」と表示されます。

### 起動する

仮想環境が有効な状態（行の先頭に `(.venv)` と出ている状態）で実行します。
2回目以降は、`source .venv/bin/activate`（Windowsは `.venv\Scripts\Activate.ps1`）をしてから起動してください。

```bash
python app.py
```

ブラウザで <http://127.0.0.1:8000/> を開くと、ダッシュボードが表示されます。
止めるときはターミナルで `Ctrl + C` を押します。

> ポート8000番がほかのアプリで使われていて起動できないときは、
> `flask --app app run --port 8001` のように別の番号で起動できます。

### 表示を確かめる

- **夜間表示**：`config.py` の `NIGHT_START` を今の時刻の少し前（例：今が14:30なら `"14:00"`）、
  `NIGHT_END` を少し後（例：`"15:00"`）にして、サーバーを起動し直してから画面を再読み込みします。
  黒い背景に時計だけが出れば成功です。確認が終わったら元に戻してください。
- **スマホ向けの表示**：ブラウザの幅を狭くすると、時計・カレンダー・パネルが縦に並びます。

### テストを動かす

```bash
pytest
```

## 2. Notion連携の準備

カレンダーには、部内Notionのカレンダー用データベースの予定を表示します。
Notionの「インテグレーション」（外部のプログラムがNotionを読むための仕組み）を作り、
そのトークンとデータベースIDを `.env` に書きます。

### (1) インテグレーションを作る

1. <https://www.notion.so/profile/integrations> を開き、「新しいインテグレーション」を押します。
2. 名前（例：`部室ダッシュボード`）を入れ、部のワークスペースを選んで保存します。
3. 「機能」（Capabilities）で **「コンテンツを読み取る」だけ** にチェックを入れ、ほかは外して保存します。
   このダッシュボードはNotionに書き込まないので、読み取りだけで十分です。
4. 「内部インテグレーションシークレット」（`ntn_` で始まる文字列）をコピーし、
   `.env` の `NOTION_TOKEN=` の後ろに貼ります。

> このトークンは、カレンダーを読むための鍵です。Git、Slack、チャット、AIへの質問などに貼らないでください。
> 漏れたかもしれないときは、上の画面で「再発行」してから `.env` を書き換えます。

### (2) カレンダーのデータベースに接続する

インテグレーションは、接続したページやデータベースしか読めません。

1. Notionでカレンダー用のデータベースを（ページ全体で）開きます。
2. 右上の「…」→「接続」（Connections）→ (1) で作ったインテグレーションを選びます。

カレンダーのデータベース **だけ** に接続してください（部のトップページなどに接続すると、その中のすべてが読めてしまいます）。

### (3) データベースIDを調べる

データベースをページ全体で開いたときのURLは、次のような形になっています。

```text
https://www.notion.so/<ワークスペース名>/<32文字の英数字>?v=<ビューのID>
```

`?v=` の前にある **32文字の英数字** がデータベースIDです。`.env` の `NOTION_DATABASE_ID=` の後ろに貼ります。
（URLに `部室カレンダー-0123abcd...` のように名前が付いているときは、最後の32文字だけを使います。）

### (4) タップしたときに開くURLを決める

カレンダーをタップしたときに開くURLを `.env` の `NOTION_CALENDAR_OPEN_URL=` に書きます。
ふつうは (3) で開いたデータベースのURLをそのまま貼ればよいです。

iPadでNotionアプリではなくSafariが開いてしまう場合は、先頭の `https://` を `notion://` に書き換えます。

```text
NOTION_CALENDAR_OPEN_URL=notion://www.notion.so/<ワークスペース名>/<32文字の英数字>
```

### (5) プロパティ名を合わせる

このダッシュボードは、予定のタイトルを「名前」、日付を「日付」という名前のプロパティ（データベースの列）から読みます。
Notionの列名が違うときは、`config.py` の次の2行を、Notionの列名に合わせて書き換えます。

```python
NOTION_TITLE_PROPERTY = "名前"
NOTION_DATE_PROPERTY = "日付"
```

### (6) 確かめる

サーバーを起動し直して画面を開き、今月の予定が出れば完了です。
「Notionが未設定です」と出るときは `.env` の書き方を、
「予定を取得できません」と出るときは下の「よくあるトラブルと対処」を見てください。

### カレンダーの動き

- 今月を月表示で出します。月が変わると自動で次の月になります（最大で `CALENDAR_REFRESH_SECONDS` 秒＝10分遅れ）。
- 予定は10分ごとに取り直します。サーバーはNotionの結果を5分間使い回すので、Notionに予定を足してから画面に出るまで最大で15分ほどかかります。急ぐときは画面を再読み込みしてください（それでも最大5分）。
- Notionやネットにつながらないときは、前回の予定を残したまま、カレンダーの右上に「最終更新 14:30」と赤字で出ます。
- 表示する月より前に始まった予定は、31日前に始まったものまで探します。それより長い予定を出したいときは、`config.py` の `NOTION_LOOKBACK_DAYS` を大きくします。

## 3. ラズパイへの設置

ステップ4で追記します（systemd による自動起動と、cron によるセンサー値の収集）。

## 4. 家から見られるようにする

ステップ5で追記します（Cloudflare Tunnel と Cloudflare Access）。
大学ネットワークの規程の確認と、ドメインの用意が済むまでは行いません。

## 5. パネルの追加方法

右側の枠に出す「パネル」は、次の4つを用意すると追加できます。
ここでは例として、文字を1行出すだけの「お知らせ」パネル（パネルID：`message`）を作ります。
パネルIDは英小文字とアンダースコア（`_`）で付けてください。

### (1) データを作る Python ファイル：`panels/message.py`

API が返すデータ（辞書）を作る関数 `get_data()` を書きます。

```python
# このファイルの役割：
#   お知らせパネルの API が返すデータを作ります。

def get_data():
    return {"text": "部室の鍵は18時までに返却してください"}
```

### (2) API の URL：`app.py`

`app.py` の先頭の import の並び（`import notion_calendar` の下）にパネルのファイルを足し、
「API（JSONを返すURL）」の場所に関数を1つ足します。URL は必ず `/api/panels/<パネルID>` にします。

```python
from panels import message
```

```python
@app.route("/api/panels/message")
def api_panel_message():
    return jsonify(message.get_data())
```

ブラウザで <http://127.0.0.1:8000/api/panels/message> を開き、JSON が表示されればここまで成功です。

### (3) 表示用のテンプレート：`templates/panels/message.html`

パネルの中身の HTML と、「API のデータをどう表示するか」を書きます。
`registerPanel("<パネルID>", 関数)` で登録した関数が、データを取るたび（初期値は1分ごと）に呼ばれます。
関数の `body` はこのパネルの中身の要素、`data` は (1) で作ったデータです。

```html
{# このファイルの役割：お知らせパネルの表示部分です。 #}
<p class="message-text"></p>
<script>
  registerPanel("message", function (body, data) {
    body.querySelector(".message-text").textContent = data.text;
  });
</script>
```

> 文字を画面に入れるときは `innerHTML` ではなく `textContent` を使ってください。
> データに `<` などが入っていても、そのまま文字として表示されて安全です。

### (4) 枠に登録する：`config.py`

`PANELS` の、表示したい枠の `None` を書き換えます。

```python
PANELS = [
    None,  # 準備中
    {"id": "message", "title": "お知らせ"},
    None,  # 準備中
]
```

サーバーを起動し直して画面を開くと、枠2に「お知らせ」が表示されます。

データの取得に失敗したとき（API がエラーを返した、サーバーが止まった など）は、
前回の表示を残したまま、パネルの右上に「最終更新 14:30」のように最後に成功した時刻が赤字で出ます。
1つのパネルが失敗しても、ほかのパネルには影響しません。

## 6. センサーの追加方法

ステップ3（水耕栽培）で追記します。

## 7. よくあるトラブルと対処

| 症状 | 確認すること |
| --- | --- |
| `python app.py` で `Address already in use` と出る | ポート8000番がほかのアプリで使われています。そのアプリを止めるか、`flask --app app run --port 8001` で別の番号を使ってください |
| `ModuleNotFoundError: No module named 'flask'` | 仮想環境が有効になっていません。`source .venv/bin/activate`（Windowsは `.venv\Scripts\Activate.ps1`）を実行してください |
| 画面の時計が止まっている・更新されない | ブラウザで再読み込みしてください。直らなければ、ブラウザの開発者ツールの「コンソール」に赤いエラーが出ていないか見てください |
| パネルに「データを取得できません」と出る | ブラウザで `/api/panels/<パネルID>` を直接開き、エラーになっていないか確認してください。サーバー側のエラーは `logs/app.log` とターミナルに出ます |
| カレンダーの下に「Notionが未設定です」と出る | `.env` がこのフォルダ（`app.py` と同じ場所）にあり、`NOTION_TOKEN` と `NOTION_DATABASE_ID` が書かれているか確認してください。書き換えたらサーバーを起動し直します |
| カレンダーに「予定を取得できません」と出る | `logs/app.log` を開き、最後のほうのエラーを見てください。よくある原因は下の3つです |
| ログに `Could not find database` / `object_not_found` | データベースIDが違うか、インテグレーションをデータベースに接続していません（「2. Notion連携の準備」の(2)(3)） |
| ログに `API token is invalid` / `unauthorized` | `NOTION_TOKEN` が違います。コピーし直すか、再発行してください |
| ログに `プロパティ「〜」がありません` | Notionの列名と `config.py` の `NOTION_TITLE_PROPERTY` / `NOTION_DATE_PROPERTY` が一致していません |
| 予定が出ない（エラーもない） | その予定に日付が入っているか、日付の列が `NOTION_DATE_PROPERTY` の列か確認してください。Notionに足したばかりなら、最大15分待つか再読み込みしてください |
| カレンダーをタップしてもNotionが開かない | `.env` の `NOTION_CALENDAR_OPEN_URL` が空になっていないか確認してください。iPadでSafariが開いてしまうときは `notion://` で始まる形にします |
| 追加したパネルで `TemplateNotFound` エラーになる | `templates/panels/<パネルID>.html` のファイル名と、`config.py` の `id` が一致しているか確認してください |
