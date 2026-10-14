# このファイルの役割：
#   ダッシュボードの画面（/）が正しく表示されるかを確かめるテストです。
#   リポジトリのルートで `pytest` を実行すると動きます。

from apps.dashboard import app as app_module
from apps.dashboard import config


def test_index_shows_three_empty_frames(monkeypatch):
    """PANELS がすべて None なら、「準備中」の枠が3つ表示される。"""
    monkeypatch.setattr(config, "PANELS", [None, None, None])
    client = app_module.app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert html.count("panel-empty") == 3
    assert "準備中" in html
