// このファイルの役割：
//   画面左側のカレンダー（FullCalendar の月表示）を表示し、定期的に予定を取り直します。
//   - 予定はサーバーの /api/calendar から取得する（サーバーがNotionから取ってくる）
//   - 取得に失敗したら、前回の予定を残したまま「最終更新 14:30」を出す
//   - 月が変わったら、自動で新しい月を表示する
//   - カレンダーをタップすると、.env の NOTION_CALENDAR_OPEN_URL を開く
//   CONFIG と getTimeText() は dashboard.js で用意しているものを使います。

document.addEventListener("DOMContentLoaded", function () {
  const calendarElement = document.getElementById("calendar");
  const statusElement = document.querySelector(".calendar-status");

  let lastEvents = []; // 最後に取得に成功した予定
  let lastSuccessTime = null; // 最後に取得に成功した時刻（"14:30" の形）

  // FullCalendar が予定を必要とするたびに呼ばれる関数。
  // info.startStr / info.endStr は表示期間（例: "2026-09-27T00:00:00+09:00"）で、
  // 先頭の日付部分（10文字）を API に渡す。
  async function loadEvents(info, successCallback) {
    const url =
      "/api/calendar?start=" + info.startStr.slice(0, 10) + "&end=" + info.endStr.slice(0, 10);
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      lastEvents = await response.json();
      lastSuccessTime = getTimeText();
      statusElement.textContent = "";
      statusElement.classList.remove("is-error");
    } catch (error) {
      console.error("カレンダーの予定の取得に失敗しました:", error);
      statusElement.classList.add("is-error");
      if (lastSuccessTime) {
        statusElement.textContent = "最終更新 " + lastSuccessTime;
      } else {
        statusElement.textContent = "予定を取得できません";
      }
    }
    // 失敗したときも前回の予定を渡して、表示が消えないようにする
    successCallback(lastEvents);
  }

  const calendar = new FullCalendar.Calendar(calendarElement, {
    initialView: "dayGridMonth", // 月表示
    locale: "ja", // 日本語で表示
    timeZone: CONFIG.timezone, // 日本時間で表示
    headerToolbar: { left: "title", center: "", right: "" }, // 「2026年10月」の見出しだけ（前月・翌月ボタンなし）
    height: "100%", // 枠の高さいっぱいに広げる
    dayMaxEvents: true, // 1日に予定が入りきらないときは「他 2 件」のようにまとめる
    moreLinkClick: function () {}, // 「他 2 件」を押しても一覧は開かない（カレンダー全体のタップでNotionを開くため）
    displayEventEnd: false, // 時刻つきの予定は開始時刻だけを出す（狭いマスで読みやすくするため）
    eventTimeFormat: { hour: "2-digit", minute: "2-digit", hour12: false }, // 時刻を "18:00" の形で出す
    // 日付のマスは「4日」ではなく「4」と数字だけを出す（狭いマスで読みやすくするため）
    dayCellContent: function (arg) {
      return arg.dayNumberText.replace("日", "");
    },
    events: loadEvents,
  });
  calendar.render();

  // 定期的に、今月を表示し直してから予定を取り直す。
  // 月が変わっていれば today() で新しい月に移動する（同じ月なら何も変わらない）。
  setInterval(function () {
    calendar.today();
    calendar.refetchEvents();
  }, CONFIG.calendarRefreshSeconds * 1000);

  // カレンダーのどこをタップしても、設定したURL（Notion）を開く。
  // URLは https://〜 でも notion://〜 でも動くよう、手を加えずにそのまま使う。
  calendarElement.addEventListener("click", function () {
    if (CONFIG.calendarOpenUrl) {
      window.location.href = CONFIG.calendarOpenUrl;
    }
  });
});
