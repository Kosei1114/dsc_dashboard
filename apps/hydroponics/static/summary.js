// このファイルの役割：
//   要約APIのデータを表示します。専用画面とダッシュボードのパネルで共用します。
//   外部の文字列はすべて textContent で入れ、HTMLとして扱いません。

window.renderHydroponicsSummary = function (root, data, options = {}) {
  const labels = { ok: "正常", warn: "注意", danger: "危険", system: "システム異常" };
  if (!Object.prototype.hasOwnProperty.call(labels, data.overall) || !Array.isArray(data.items) || !Array.isArray(data.actions)) {
    throw new Error("水耕栽培の要約データの形式が正しくありません");
  }

  // 描画が完了するまでは前回の表示を残し、最後にまとめて差し替えます。
  const content = document.createDocumentFragment();
  function add(parent, tag, className, text) {
    const element = document.createElement(tag);
    element.className = className;
    element.textContent = text;
    parent.appendChild(element);
    return element;
  }
  function timeText(value) {
    return new Date(value).toLocaleTimeString("ja-JP", {
      timeZone: "Asia/Tokyo", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    });
  }

  add(content, "p", "hydro-state hydro-state-" + data.overall,
    data.measured_at ? labels[data.overall] : "未計測");
  if (!data.measured_at) {
    add(content, "p", "hydro-empty", "まだ計測データがありません");
    root.replaceChildren(content);
    return;
  }

  const maxActions = options.maxActions ?? data.actions.length;
  const actions = add(content, "ul", "hydro-actions", "");
  for (const action of data.actions.slice(0, maxActions)) {
    add(actions, "li", "hydro-action", action.text);
  }
  if (data.actions.length > maxActions) {
    add(actions, "li", "hydro-more", "他 " + (data.actions.length - maxActions) + "件");
  }

  const metrics = add(content, "dl", "hydro-metrics", "");
  const maxItems = options.maxItems ?? data.items.length;
  for (const item of data.items.slice(0, maxItems)) {
    const row = add(metrics, "div", "hydro-metric hydro-metric-" + item.status, "");
    add(row, "dt", "", item.label);
    let valueText = "—";
    if (item.status === "stale") {
      valueText += item.measured_at ? " 欠測（" + timeText(item.measured_at) + "より更新なし）" : " 欠測";
    } else if (item.status === "sensor_error") {
      valueText += " 異常";
    } else if (typeof item.value === "number" && Number.isFinite(item.value)) {
      valueText = item.value.toFixed(item.metric === "ec" ? 2 : 1) + " " + item.unit;
    }
    add(row, "dd", "", valueText);
  }
  add(content, "p", "hydro-measured", data.stale
    ? "データが届いていません" : timeText(data.measured_at) + " 計測");
  root.replaceChildren(content);
};
