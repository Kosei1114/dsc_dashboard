# このファイルの役割：水耕栽培アプリ単体でも、画面とAPIのURLが正しく動くことを確認します。

from apps.hydroponics import config
from apps.hydroponics.app import app
from tests.html_helpers import Elements, hydro_js_config


def test_unmeasured_api_does_not_invent_sensor_values():
    response = app.test_client().get("/api/summary")
    assert response.status_code == 200
    data = response.get_json()
    assert data["measured_at"] is None
    assert data["stale"] is True
    assert data["overall"] == "system"
    assert data["items"] == []


def test_standalone_urls_and_optional_dashboard_link(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_URL", "")
    client = app.test_client()
    response = client.get("/?from=dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    js_config = hydro_js_config(html)
    assert js_config["summaryUrl"] == "/api/summary"
    assert js_config["idleReturnSeconds"] == 0
    assert "ダッシュボードに戻る" not in html
    for tag, attrs in Elements(html).elements:
        if tag == "script" and attrs.get("src"):
            assert client.get(attrs["src"]).status_code == 200

    monkeypatch.setattr(config, "DASHBOARD_URL", "https://dashboard.example.test/")
    html = client.get("/?from=dashboard").get_data(as_text=True)
    assert hydro_js_config(html)["dashboardUrl"] == "https://dashboard.example.test/"
    assert hydro_js_config(html)["idleReturnSeconds"] == 180
    assert hydro_js_config(client.get("/").get_data(as_text=True))["idleReturnSeconds"] == 0
