# 部室アプリ

アプリを `apps/` 配下で管理します。ダッシュボードは `apps/dashboard/`、
水耕栽培のセンサー処理は `apps/hydroponics/` に置きます。
各アプリの画面・設定・データ処理は、それぞれのフォルダで管理します。

## 起動

以下はリポジトリのルートで実行します。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp apps/dashboard/.env.example apps/dashboard/.env
python app.py
```

ダッシュボードは `http://127.0.0.1:8000/` で開きます。
Notionの設定は `apps/dashboard/.env` に書きます。
詳しい説明は [ダッシュボードのREADME](apps/dashboard/README.md) を参照してください。
単体で起動する場合は `python -m apps.dashboard.app` も使えます。

## 確認

```bash
pytest
```
