# このファイルの役割：
#   Notionカレンダー（notion_calendar.py と /api/calendar）のテストです。
#   本物のNotionには接続せず、Notionが返すデータを真似した「偽物」を使って確かめます。
#   リポジトリのルートで `pytest` を実行すると動きます。

from datetime import date

import pytest

import app as app_module
import config
import notion_calendar


def make_page(title, start, end=None):
    """Notionが返すページ（予定1件）を真似したデータを作る。"""
    return {
        "properties": {
            "名前": {"title": [{"plain_text": title}] if title else []},
            "日付": {"date": {"start": start, "end": end, "time_zone": None}},
        }
    }


@pytest.fixture(autouse=True)
def reset_settings(monkeypatch):
    """テストごとに、設定とメモリ上の保存結果を初期状態に戻す。"""
    monkeypatch.setattr(config, "NOTION_TITLE_PROPERTY", "名前")
    monkeypatch.setattr(config, "NOTION_DATE_PROPERTY", "日付")
    monkeypatch.setattr(config, "TIMEZONE", "Asia/Tokyo")
    monkeypatch.setattr(config, "NOTION_TOKEN", "dummy-token")
    monkeypatch.setattr(config, "NOTION_DATABASE_ID", "dummy-database")
    monkeypatch.setattr(notion_calendar, "_cache", {})


# ===== 予定1件の変換（page_to_event） =====


def test_all_day_single_day_ends_next_day():
    """1日だけの終日予定は、終了日が翌日になる。"""
    event = notion_calendar.page_to_event(make_page("部会", "2026-10-04"))
    assert event == {"title": "部会", "start": "2026-10-04", "end": "2026-10-05", "allDay": True}


def test_all_day_multi_day_end_is_shifted_by_one_day():
    """Notionで10/10〜10/12（3日間）の終日予定は、FullCalendarの終了日が10/13になる。"""
    event = notion_calendar.page_to_event(make_page("合宿", "2026-10-10", "2026-10-12"))
    assert event["start"] == "2026-10-10"
    assert event["end"] == "2026-10-13"
    assert event["allDay"] is True


def test_all_day_across_month_end():
    """月末をまたぐ終日予定も、正しく1日後ろにずれる。"""
    event = notion_calendar.page_to_event(make_page("学園祭", "2026-10-30", "2026-10-31"))
    assert event["end"] == "2026-11-01"


def test_timed_event_is_passed_through():
    """時刻つきの予定は、開始・終了をそのまま渡す。"""
    page = make_page("定例会", "2026-10-04T18:00:00.000+09:00", "2026-10-04T19:30:00.000+09:00")
    event = notion_calendar.page_to_event(page)
    assert event == {
        "title": "定例会",
        "start": "2026-10-04T18:00:00.000+09:00",
        "end": "2026-10-04T19:30:00.000+09:00",
        "allDay": False,
    }


def test_timed_event_without_end():
    page = make_page("締切", "2026-10-04T23:59:00.000+09:00")
    event = notion_calendar.page_to_event(page)
    assert event["end"] is None
    assert event["allDay"] is False


def test_page_without_date_is_skipped():
    page = make_page("日付なし", "2026-10-04")
    page["properties"]["日付"]["date"] = None
    assert notion_calendar.page_to_event(page) is None


def test_empty_title():
    event = notion_calendar.page_to_event(make_page("", "2026-10-04"))
    assert event["title"] == "（無題）"


def test_title_made_of_several_parts():
    """太字などで分かれたタイトルは、つなげて1つにする。"""
    page = make_page("x", "2026-10-04")
    page["properties"]["名前"]["title"] = [{"plain_text": "新歓"}, {"plain_text": "BBQ"}]
    assert notion_calendar.page_to_event(page)["title"] == "新歓BBQ"


def test_property_names_come_from_config(monkeypatch):
    """プロパティ名は config.py の設定で変えられる。"""
    monkeypatch.setattr(config, "NOTION_TITLE_PROPERTY", "Name")
    monkeypatch.setattr(config, "NOTION_DATE_PROPERTY", "Date")
    page = {
        "properties": {
            "Name": {"title": [{"plain_text": "Meeting"}]},
            "Date": {"date": {"start": "2026-10-04", "end": None}},
        }
    }
    assert notion_calendar.page_to_event(page)["title"] == "Meeting"


def test_missing_property_gives_helpful_error():
    page = {"properties": {"Name": {"title": []}}}
    with pytest.raises(KeyError, match="NOTION_TITLE_PROPERTY"):
        notion_calendar.page_to_event(page)


# ===== 表示期間に重なるかの判定（pages_to_events） =====

# 2026年10月の月表示は 9/27(日)〜11/7(土)。FullCalendar の end は含まないので 11/8 になる
RANGE_START = date(2026, 9, 27)
RANGE_END = date(2026, 11, 8)


def titles_in_range(pages):
    return [e["title"] for e in notion_calendar.pages_to_events(pages, RANGE_START, RANGE_END)]


def test_event_starting_before_range_but_ending_inside_is_included():
    """表示期間より前に始まり、表示期間の中で終わる予定は表示する。"""
    assert titles_in_range([make_page("長期休み", "2026-09-01", "2026-09-27")]) == ["長期休み"]


def test_event_ending_before_range_is_excluded():
    """表示期間の前日に終わる予定は表示しない。"""
    assert titles_in_range([make_page("前の月", "2026-09-20", "2026-09-26")]) == []


def test_event_starting_on_range_end_is_excluded():
    """表示期間の終わり（その日を含まない）に始まる予定は表示しない。"""
    assert titles_in_range([make_page("次の月", "2026-11-08")]) == []


def test_event_on_last_visible_day_is_included():
    assert titles_in_range([make_page("最終日", "2026-11-07")]) == ["最終日"]


def test_timed_event_late_on_last_visible_day_is_included():
    """表示期間の最終日の夜（日本時間）の予定も表示する。"""
    assert titles_in_range([make_page("夜", "2026-11-07T23:30:00.000+09:00")]) == ["夜"]


def test_timed_event_in_utc_is_compared_in_japan_time():
    """UTC で書かれた時刻も、日本時間に直して比べる（11/7 15:00 UTC = 11/8 0:00 日本時間）。"""
    assert titles_in_range([make_page("UTC", "2026-11-07T15:00:00.000Z")]) == []


# ===== Notionへの問い合わせ（fetch_pages） =====


class FakeNotionClient:
    """notion_client.Client の代わりに使う偽物。問い合わせの内容を記録し、決まった結果を返す。"""

    def __init__(self, pages, page_size=100):
        self.pages = pages
        self.page_size = page_size
        self.query_calls = []
        self.databases = self
        self.data_sources = self

    # client.databases.retrieve(...) の代わり
    def retrieve(self, database_id):
        assert database_id == "dummy-database"
        return {"data_sources": [{"id": "dummy-data-source", "name": "カレンダー"}]}

    # client.data_sources.query(...) の代わり。page_size 件ずつに分けて返す
    def query(self, data_source_id, filter, start_cursor=None):
        self.query_calls.append({"data_source_id": data_source_id, "filter": filter})
        begin = int(start_cursor or 0)
        finish = begin + self.page_size
        has_more = finish < len(self.pages)
        return {
            "results": self.pages[begin:finish],
            "has_more": has_more,
            "next_cursor": str(finish) if has_more else None,
        }


def use_fake_client(monkeypatch, fake):
    monkeypatch.setattr(notion_calendar, "Client", lambda **kwargs: fake)


def test_fetch_pages_gets_all_pages_beyond_100(monkeypatch):
    """1回の上限（100件）を超えたら、続きも取得する。"""
    pages = [make_page(f"予定{i}", "2026-10-04") for i in range(250)]
    fake = FakeNotionClient(pages)
    use_fake_client(monkeypatch, fake)

    result = notion_calendar.fetch_pages(RANGE_START, RANGE_END)

    assert len(result) == 250
    assert len(fake.query_calls) == 3  # 100件 + 100件 + 50件
    assert fake.query_calls[0]["data_source_id"] == "dummy-data-source"


def test_fetch_pages_filters_by_date_property(monkeypatch):
    monkeypatch.setattr(config, "NOTION_LOOKBACK_DAYS", 31)
    fake = FakeNotionClient([])
    use_fake_client(monkeypatch, fake)

    notion_calendar.fetch_pages(RANGE_START, RANGE_END)

    conditions = fake.query_calls[0]["filter"]["and"]
    assert {"property": "日付", "date": {"on_or_after": "2026-08-27"}} in conditions
    assert {"property": "日付", "date": {"on_or_before": "2026-11-08"}} in conditions


# ===== 結果の使い回しと、失敗したときの動き（get_events） =====


def test_results_are_reused_within_cache_time(monkeypatch):
    calls = []

    def fake_fetch(range_start, range_end):
        calls.append(1)
        return [make_page("部会", "2026-10-04")]

    monkeypatch.setattr(notion_calendar, "fetch_pages", fake_fetch)
    first = notion_calendar.get_events(RANGE_START, RANGE_END)
    second = notion_calendar.get_events(RANGE_START, RANGE_END)

    assert first == second
    assert len(calls) == 1  # 2回目はNotionに問い合わせていない


def test_last_result_is_returned_when_notion_fails(monkeypatch):
    monkeypatch.setattr(config, "CALENDAR_CACHE_SECONDS", 0)  # 毎回問い合わせる設定にする
    monkeypatch.setattr(notion_calendar, "fetch_pages", lambda s, e: [make_page("部会", "2026-10-04")])
    first = notion_calendar.get_events(RANGE_START, RANGE_END)

    def broken_fetch(range_start, range_end):
        raise ConnectionError("ネットにつながらない")

    monkeypatch.setattr(notion_calendar, "fetch_pages", broken_fetch)
    second = notion_calendar.get_events(RANGE_START, RANGE_END)

    assert second == first


def test_error_is_raised_when_notion_fails_without_previous_result(monkeypatch):
    def broken_fetch(range_start, range_end):
        raise ConnectionError("ネットにつながらない")

    monkeypatch.setattr(notion_calendar, "fetch_pages", broken_fetch)
    with pytest.raises(ConnectionError):
        notion_calendar.get_events(RANGE_START, RANGE_END)


# ===== API（/api/calendar） =====


@pytest.fixture
def client():
    return app_module.app.test_client()


def test_api_returns_events(client, monkeypatch):
    monkeypatch.setattr(
        notion_calendar, "fetch_pages", lambda s, e: [make_page("合宿", "2026-10-10", "2026-10-12")]
    )
    response = client.get("/api/calendar?start=2026-09-27&end=2026-11-08")

    assert response.status_code == 200
    assert response.get_json() == [
        {"title": "合宿", "start": "2026-10-10", "end": "2026-10-13", "allDay": True}
    ]


def test_api_accepts_fullcalendar_datetime_format(client, monkeypatch):
    """FullCalendar が "2026-09-27T00:00:00+09:00" の形で渡しても動く。"""
    received = []
    monkeypatch.setattr(
        notion_calendar, "get_events", lambda s, e: received.append((s, e)) or []
    )
    response = client.get(
        "/api/calendar",
        query_string={"start": "2026-09-27T00:00:00+09:00", "end": "2026-11-08T00:00:00+09:00"},
    )
    assert response.status_code == 200
    assert received == [(RANGE_START, RANGE_END)]


def test_api_returns_empty_list_when_notion_is_not_configured(client, monkeypatch):
    monkeypatch.setattr(config, "NOTION_TOKEN", "")
    response = client.get("/api/calendar?start=2026-09-27&end=2026-11-08")
    assert response.status_code == 200
    assert response.get_json() == []


def test_api_rejects_bad_dates(client):
    response = client.get("/api/calendar?start=yesterday&end=2026-11-08")
    assert response.status_code == 400


def test_api_returns_502_when_notion_fails(client, monkeypatch):
    def broken_fetch(range_start, range_end):
        raise ConnectionError("ネットにつながらない")

    monkeypatch.setattr(notion_calendar, "fetch_pages", broken_fetch)
    response = client.get("/api/calendar?start=2026-09-27&end=2026-11-08")
    assert response.status_code == 502


def test_index_shows_notice_when_notion_is_not_configured(client, monkeypatch):
    monkeypatch.setattr(config, "NOTION_TOKEN", "")
    html = client.get("/").get_data(as_text=True)
    assert "Notionが未設定です" in html


def test_token_is_not_sent_to_browser(client):
    """Notionのトークンが画面のHTMLに含まれていない。"""
    html = client.get("/").get_data(as_text=True)
    assert "dummy-token" not in html
