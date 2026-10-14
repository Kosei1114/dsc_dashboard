// このファイルの役割：専用画面の定期更新と、ダッシュボードから開いたときの自動復帰です。
const HYDRO_CONFIG = window.HYDROPONICS_CONFIG;
let lastSuccess = null;

async function refreshSummary() {
  const status = document.getElementById("update-status");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), HYDRO_CONFIG.fetchTimeoutSeconds * 1000);
  try {
    const response = await fetch(HYDRO_CONFIG.summaryUrl, { signal: controller.signal });
    if (!response.ok) throw new Error("HTTP " + response.status);
    window.renderHydroponicsSummary(document.getElementById("summary"), await response.json());
    lastSuccess = new Date().toLocaleTimeString("ja-JP", {
      timeZone: "Asia/Tokyo", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    });
    status.textContent = "";
    status.classList.remove("is-error");
  } catch (error) {
    console.error("水耕栽培の更新に失敗しました:", error);
    status.textContent = lastSuccess ? "最終更新 " + lastSuccess : "データを取得できません";
    status.classList.add("is-error");
  } finally {
    clearTimeout(timeout);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  refreshSummary();
  setInterval(refreshSummary, HYDRO_CONFIG.refreshSeconds * 1000);

  // 直接アプリを開いた場合は戻さず、ダッシュボードから来た場合だけ戻します。
  if (HYDRO_CONFIG.idleReturnSeconds && HYDRO_CONFIG.dashboardUrl) {
    let returnTimer;
    function resetReturnTimer() {
      clearTimeout(returnTimer);
      returnTimer = setTimeout(() => window.location.assign(HYDRO_CONFIG.dashboardUrl),
        HYDRO_CONFIG.idleReturnSeconds * 1000);
    }
    for (const event of ["pointerdown", "pointermove", "keydown", "scroll"]) {
      document.addEventListener(event, resetReturnTimer, { passive: true, capture: true });
    }
    resetReturnTimer();
  }
});
