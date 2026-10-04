// このファイルの役割：
//   ダッシュボード画面で動く JavaScript です。
//   - 右上の時計を進める
//   - 夜間の時間帯に「夜間表示」（黒い背景に時計だけ）へ切り替える
//   - 各パネルのデータを API から定期的に取り直して、画面を書き換える
//   設定値（更新間隔や夜間の時間帯）は config.py にあり、index.html 経由で受け取ります。

// サーバーから受け取った設定（templates/index.html で用意している）
const CONFIG = window.DASHBOARD_CONFIG;

// ===== 時刻の扱い =====

// 設定したタイムゾーン（日本時間）での今の日時を、部品ごとに取り出す。
// 戻り値の例: { month: "10", day: "4", weekday: "日", hour: "14", minute: "32" }
function getNowParts() {
  const formatter = new Intl.DateTimeFormat("ja-JP", {
    timeZone: CONFIG.timezone,
    month: "numeric",
    day: "numeric",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23", // 0〜23時で表す（"24:05" のような表示を防ぐ）
  });
  const parts = {};
  for (const part of formatter.formatToParts(new Date())) {
    parts[part.type] = part.value;
  }
  return parts;
}

// 今の時刻を "14:32" の形で返す
function getTimeText() {
  const now = getNowParts();
  return now.hour + ":" + now.minute;
}

// "14:32" のような時刻が夜間の時間帯に入っているかを調べる。
// "HH:MM" の形の文字列は、そのまま大小を比べれば時刻の前後と一致する。
function isNightTime(timeText) {
  const start = CONFIG.nightStart;
  const end = CONFIG.nightEnd;
  if (start <= end) {
    // 例: 01:00〜05:00 のように日をまたがない場合
    return start <= timeText && timeText < end;
  }
  // 例: 22:00〜07:00 のように日をまたぐ場合
  return timeText >= start || timeText < end;
}

// ===== 時計と夜間表示 =====

function updateClock() {
  const now = getNowParts();
  const text = now.month + "/" + now.day + "(" + now.weekday + ") " + now.hour + ":" + now.minute;
  // 時計は「右上」と「夜間表示」の2か所にある
  for (const element of document.querySelectorAll(".clock")) {
    element.textContent = text;
  }
  // body に night というクラスを付けると、style.css の設定で夜間表示になる
  document.body.classList.toggle("night", isNightTime(getTimeText()));
}

// ===== パネル =====

// パネルIDごとの「データを画面に描く関数」を入れておく場所
const panelRenderers = {};

// パネルのテンプレート（templates/panels/<パネルID>.html）から呼び出して、
// 「APIから受け取ったデータをどう画面に描くか」を登録する。
//   panelId:        パネルID（例: "hydroponics"）
//   renderFunction: function (body, data) { ... } の形の関数。
//                   body はパネルの中身の要素、data は API が返した JSON
function registerPanel(panelId, renderFunction) {
  panelRenderers[panelId] = renderFunction;
}

// 1つのパネルのデータを API から取り直して描き直す。
// 失敗しても前回の表示は残し、「最終更新 14:30」のように最後に成功した時刻を出す。
async function refreshPanel(panelElement) {
  const panelId = panelElement.dataset.panelId;
  const statusElement = panelElement.querySelector(".panel-status");
  try {
    const renderFunction = panelRenderers[panelId];
    if (!renderFunction) {
      throw new Error("registerPanel(\"" + panelId + "\", ...) が見つかりません");
    }
    const response = await fetch("/api/panels/" + panelId);
    if (!response.ok) {
      throw new Error("HTTP " + response.status);
    }
    const data = await response.json();
    renderFunction(panelElement.querySelector(".panel-body"), data);

    // 成功したら、成功した時刻を覚えておき、エラー表示を消す
    panelElement.dataset.lastSuccess = getTimeText();
    panelElement.classList.remove("is-error");
    statusElement.textContent = "";
  } catch (error) {
    console.error("パネル " + panelId + " の更新に失敗しました:", error);
    panelElement.classList.add("is-error");
    if (panelElement.dataset.lastSuccess) {
      statusElement.textContent = "最終更新 " + panelElement.dataset.lastSuccess;
    } else {
      statusElement.textContent = "データを取得できません";
    }
  }
}

// すべてのパネルを取り直す。1つが失敗しても、ほかのパネルには影響しない。
function refreshAllPanels() {
  for (const panelElement of document.querySelectorAll("[data-panel-id]")) {
    refreshPanel(panelElement);
  }
}

// ===== 起動 =====

// ページの読み込みが終わったら動き始める
document.addEventListener("DOMContentLoaded", function () {
  updateClock();
  // 時計は1秒ごとに確認する（分が変わった瞬間に表示が進むように）
  setInterval(updateClock, 1000);

  refreshAllPanels();
  setInterval(refreshAllPanels, CONFIG.panelRefreshSeconds * 1000);
});
