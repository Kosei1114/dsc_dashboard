# 部室ダッシュボード

岡山大学DS部の部室に置いたiPadに常時表示する、Webのダッシュボードです。
画面の左半分にNotionのカレンダー、右半分に時計と機能ごとの「パネル」を並べます。

仕様はリポジトリのルートにある `部室ダッシュボード 仕様書.md` を見てください。

## いまできていること

| ステップ | 内容 | 状態 |
| --- | --- | --- |
| 1. 土台 | 左右分割の画面、時計、「準備中」の枠、夜間表示、スマホ向けの縦並び | 完了 |
| 2. カレンダー | Notionの予定を月表示、タップでNotionを開く | 未実装 |
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
├── app.py             # Flaskアプリ。画面とAPIのURLをここに並べる
├── panels/            # パネルごとの「APIが返すデータを作る」Pythonファイル
├── templates/         # 画面のHTML（Jinja2テンプレート）
│   ├── base.html      # 全画面に共通する骨組み
│   ├── index.html     # ダッシュボード
│   └── panels/        # パネルの中身のHTML（empty.html は「準備中」の枠）
├── static/
│   ├── style.css      # 見た目（色、文字の大きさ、配置）
│   └── dashboard.js   # 時計、夜間表示、パネルの定期更新
├── tests/             # pytest のテスト
└── logs/              # ログ（Git管理外。起動すると自動で作られる）
```

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

`app.py` の先頭の import にパネルのファイルを足し、
「API（JSONを返すURL）」の場所に関数を1つ足します。URL は必ず `/api/panels/<パネルID>` にします。

```python
from flask import Flask, jsonify, render_template  # jsonify を足す

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

## 7. よくあるトラブルと対処

| 症状 | 確認すること |
| --- | --- |
| `python app.py` で `Address already in use` と出る | ポート8000番がほかのアプリで使われています。そのアプリを止めるか、`flask --app app run --port 8001` で別の番号を使ってください |
| `ModuleNotFoundError: No module named 'flask'` | 仮想環境が有効になっていません。`source .venv/bin/activate`（Windowsは `.venv\Scripts\Activate.ps1`）を実行してください |
| 画面の時計が止まっている・更新されない | ブラウザで再読み込みしてください。直らなければ、ブラウザの開発者ツールの「コンソール」に赤いエラーが出ていないか見てください |
| パネルに「データを取得できません」と出る | ブラウザで `/api/panels/<パネルID>` を直接開き、エラーになっていないか確認してください。サーバー側のエラーは `logs/app.log` とターミナルに出ます |
| 追加したパネルで `TemplateNotFound` エラーになる | `templates/panels/<パネルID>.html` のファイル名と、`config.py` の `id` が一致しているか確認してください |
