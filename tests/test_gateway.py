# このファイルの役割：
#   パネルのAPI・遷移先・表示部品が、共通の入口から実際に開けることを確認します。

import pytest
from werkzeug.test import Client
from werkzeug.wrappers import Response

from app import application
from apps.dashboard import config as dashboard_config
from apps.hydroponics import config as hydro_config
from apps.hydroponics import summary
from tests.html_helpers import Elements, hydro_js_config


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(dashboard_config, "NOTION_TOKEN", "")
    monkeypatch.setattr(hydro_config, "DASHBOARD_URL", "")
    return Client(application, Response)


def test_panel_opens_independent_app_and_uses_its_summary(client, monkeypatch):
    data = {
        "measured_at": "2026-10-14T14:30:00+09:00",
        "stale": False,
        "overall": "ok",
        "actions": [],
        "items": [{"metric": "water_temp", "label": "液温", "value": 20.5,
                   "unit": "℃", "status": "ok", "measured_at": "2026-10-14T14:30:00+09:00"}],
    }
    monkeypatch.setattr(summary, "get_summary", lambda: data)
    dashboard = client.get("/")
    assert dashboard.status_code == 200
    elements = Elements(dashboard.get_data(as_text=True)).elements
    panel = next(attrs for tag, attrs in elements
                 if tag == "a" and attrs.get("data-panel-id") == "hydroponics")

    assert client.get(panel["data-api-url"]).get_json() == data
    detail = client.get(panel["href"])
    assert detail.status_code == 200
    html = detail.get_data(as_text=True)
    assert "<title>水耕栽培</title>" in html
    js_config = hydro_js_config(html)
    assert client.get(js_config["summaryUrl"]).get_json() == data
    assert js_config["idleReturnSeconds"] == 180
    assert js_config["dashboardUrl"] == "/"
    assert client.get(js_config["dashboardUrl"]).status_code == 200

    # マウント後も、両画面のローカルのJS・CSSへのURLが壊れない。
    for tag, attrs in elements + Elements(html).elements:
        url = attrs.get("src") if tag == "script" else attrs.get("href") if tag == "link" else None
        if url and url.startswith("/"):
            response = client.get(url)
            assert response.status_code == 200, url
            assert "text/html" not in response.content_type, url


def test_summary_failure_does_not_break_dashboard_or_expose_exception(client, monkeypatch):
    def fail():
        raise RuntimeError("internal-secret-test-value")

    monkeypatch.setattr(summary, "get_summary", fail)
    response = client.get("/apps/hydroponics/api/summary")
    assert response.status_code == 503
    assert response.get_json() == {"error": "水耕栽培のデータを取得できませんでした"}
    assert "internal-secret-test-value" not in response.get_data(as_text=True)
    assert client.get("/").status_code == 200
    assert client.get("/api/calendar").get_json() == []
    assert client.get("/apps/hydroponics/").status_code == 200


def test_direct_app_visit_does_not_return_automatically(client):
    html = client.get("/apps/hydroponics/").get_data(as_text=True)
    assert hydro_js_config(html)["idleReturnSeconds"] == 0
    assert "ダッシュボードに戻る" in html


def test_legacy_panel_without_api_url_or_detail_url_still_renders(client, monkeypatch):
    monkeypatch.setattr(dashboard_config, "PANELS", [
        {"id": "hydroponics", "title": "水耕栽培"}, None, None,
    ])
    response = client.get("/")
    assert response.status_code == 200
    elements = Elements(response.get_data(as_text=True)).elements
    panel = next((tag, attrs) for tag, attrs in elements
                 if attrs.get("data-panel-id") == "hydroponics")
    assert panel[0] == "section"
    assert panel[1]["data-api-url"] == "/api/panels/hydroponics"
