# このファイルの役割：
#   Notionのカレンダー用データベースから予定を取り出し、
#   FullCalendar（画面のカレンダー）が読める形に変換します。
#   - 取得結果は CALENDAR_CACHE_SECONDS 秒のあいだメモリに保存し、その間はNotionに問い合わせません。
#   - Notionから取得できなかったときは、最後に取得できた結果を返します。
#   Notionのトークンはこのファイルの中だけで使い、ブラウザには渡しません。

import logging
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from notion_client import Client
from notion_client.helpers import collect_paginated_api

import config

logger = logging.getLogger(__name__)

# 取得結果を保存しておく場所。
# キーは表示期間 ("2026-09-27", "2026-11-08")、値は {"events": 予定のリスト, "fetched_at": 取得した時刻（秒）}
_cache = {}


def is_configured():
    """.env にNotionのトークンとデータベースIDが書かれていれば True。"""
    return bool(config.NOTION_TOKEN and config.NOTION_DATABASE_ID)


def get_events(range_start, range_end):
    """表示期間に重なる予定を、FullCalendarの形のリストで返す。

    range_start, range_end は date。range_end の日は含まない（FullCalendarと同じ決まり）。
    Notionから取得できなかったときは、同じ期間の前回の結果を返す。
    前回の結果もなければ、例外をそのまま投げる。
    """
    key = (range_start.isoformat(), range_end.isoformat())
    cached = _cache.get(key)

    # 保存してから CALENDAR_CACHE_SECONDS 秒たっていなければ、Notionに問い合わせずに返す
    if cached and time.time() - cached["fetched_at"] < config.CALENDAR_CACHE_SECONDS:
        return cached["events"]

    try:
        pages = fetch_pages(range_start, range_end)
        events = pages_to_events(pages, range_start, range_end)
    except Exception:
        # トークンなどの秘密情報はエラーの文章に含まれないので、そのままログに残してよい
        logger.exception("Notionから予定を取得できませんでした")
        if cached:
            logger.warning("前回取得した予定を代わりに返します")
            return cached["events"]
        raise

    _cache[key] = {"events": events, "fetched_at": time.time()}
    return events


def fetch_pages(range_start, range_end):
    """Notionに問い合わせて、表示期間のあたりにある予定（Notionのページ）をすべて取得する。"""
    # 10秒待っても返事がなければあきらめる（画面の表示を長く待たせないため）
    client = Client(auth=config.NOTION_TOKEN, timeout_ms=10_000)

    # 2025年9月からのNotion APIでは、データベースの中に「データソース」があり、
    # 予定はデータソースに対して検索する。まずデータベースの情報からデータソースのIDを調べる。
    # カレンダー用のデータベースにはデータソースが1つだけある前提で、最初のものを使う。
    database = client.databases.retrieve(database_id=config.NOTION_DATABASE_ID)
    data_source_id = database["data_sources"][0]["id"]

    # 検索の条件。
    # 開始日と終了日がある予定を、Notionがどちらの日付で比べるかは公式の説明にないため、
    # 少し広め（表示期間の NOTION_LOOKBACK_DAYS 日前から）に取得しておき、
    # 本当に表示期間に重なるかどうかは、あとで pages_to_events() が正確に判定する。
    search_from = range_start - timedelta(days=config.NOTION_LOOKBACK_DAYS)
    date_filter = {
        "and": [
            {"property": config.NOTION_DATE_PROPERTY, "date": {"on_or_after": search_from.isoformat()}},
            {"property": config.NOTION_DATE_PROPERTY, "date": {"on_or_before": range_end.isoformat()}},
        ]
    }

    # Notionは1回に最大100件までしか返さない。
    # collect_paginated_api は、100件を超えたときに続きも自動で取得して、1つのリストにまとめてくれる。
    return collect_paginated_api(
        client.data_sources.query, data_source_id=data_source_id, filter=date_filter
    )


def pages_to_events(pages, range_start, range_end):
    """Notionのページのリストを、表示期間に重なる予定だけのリストに変換する。"""
    events = []
    for page in pages:
        event = page_to_event(page)
        if event is None:
            continue
        if overlaps(event, range_start, range_end):
            events.append(event)
    return events


def page_to_event(page):
    """Notionのページ1件を、FullCalendarの予定1件（辞書）に変換する。

    戻り値の例:
      終日の予定  {"title": "合宿", "start": "2026-10-10", "end": "2026-10-13", "allDay": True}
      時刻つき    {"title": "定例会", "start": "2026-10-04T18:00:00.000+09:00",
                   "end": "2026-10-04T19:30:00.000+09:00", "allDay": False}
    日付が空のページは None を返す。
    """
    properties = page["properties"]
    for name in (config.NOTION_TITLE_PROPERTY, config.NOTION_DATE_PROPERTY):
        if name not in properties:
            raise KeyError(
                f"Notionのデータベースにプロパティ「{name}」がありません。"
                "config.py の NOTION_TITLE_PROPERTY / NOTION_DATE_PROPERTY を確認してください"
            )

    date_value = properties[config.NOTION_DATE_PROPERTY]["date"]
    if date_value is None:
        return None

    # タイトルは装飾ごとに分かれた文字のリストになっているので、つなげて1つの文字列にする
    title_parts = properties[config.NOTION_TITLE_PROPERTY]["title"]
    title = "".join(part["plain_text"] for part in title_parts)
    if title == "":
        title = "（無題）"

    start = date_value["start"]
    end = date_value["end"]  # 終了日がない予定では None
    # 時刻のない予定（"2026-10-04" のように "T" を含まない）は終日の予定
    all_day = "T" not in start

    if all_day:
        # Notionの終了日は「その日を含む」が、FullCalendarの終了日は「その日を含まない」。
        # そのため、終了日を1日後ろにずらす。
        # 例: Notionで 10/10〜10/12 の3日間 → FullCalendarには end="2026-10-13" を渡す。
        # 終了日がない（1日だけの）予定は、開始日の翌日を終了日にする。
        last_day = date.fromisoformat(end or start)
        end = (last_day + timedelta(days=1)).isoformat()

    return {"title": title, "start": start, "end": end, "allDay": all_day}


def overlaps(event, range_start, range_end):
    """予定が表示期間 [range_start, range_end) に少しでも重なっていれば True。"""
    period_start = to_datetime(range_start.isoformat())
    period_end = to_datetime(range_end.isoformat())
    event_start = to_datetime(event["start"])

    if event["end"] is None:
        # 終了時刻のない予定は、開始時刻が表示期間に入っているかだけで決める
        return period_start <= event_start < period_end

    event_end = to_datetime(event["end"])
    # 「予定が表示期間の終わりより前に始まり、表示期間の始まりより後に終わる」なら重なっている
    return event_start < period_end and event_end > period_start


def to_datetime(text):
    """"2026-10-04" や "2026-10-04T18:00:00.000+09:00" の形の文字列を、比べられる datetime にする。

    日付だけのときは、その日の0時（設定のタイムゾーン）として扱う。
    """
    timezone = ZoneInfo(config.TIMEZONE)
    if "T" not in text:
        return datetime.combine(date.fromisoformat(text), datetime.min.time(), tzinfo=timezone)
    value = datetime.fromisoformat(text)
    if value.tzinfo is None:
        # タイムゾーンが書かれていない時刻は、設定のタイムゾーンの時刻とみなす
        value = value.replace(tzinfo=timezone)
    return value
