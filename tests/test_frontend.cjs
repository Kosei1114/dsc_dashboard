// このファイルの役割：ブラウザの描画とタイマーの最低限の代役で、更新・欠測・復帰の動きを確認します。
// Node.jsの標準機能だけを使います。実ブラウザでの見た目の確認を置き換えるものではありません。
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class Element {
  constructor(tag = "div") {
    this.tag = tag;
    this.children = [];
    this.dataset = {};
    this.classes = new Set();
    this.classList = {
      add: (value) => this.classes.add(value), remove: (value) => this.classes.delete(value),
    };
  }
  set textContent(value) { this.text = String(value); this.children = []; }
  get textContent() { return (this.text || "") + this.children.map((child) => child.textContent).join(" "); }
  set innerHTML(value) { throw new Error("APIのデータをHTMLとして扱ってはいけません"); }
  appendChild(child) { this.children.push(child); }
  replaceChildren(child) { this.text = ""; this.children = child.tag === "fragment" ? child.children : [child]; }
}

function browser(config = {}) {
  const events = new Map();
  const timers = new Map();
  const summary = new Element();
  const status = new Element();
  const locations = [];
  let nextTimer = 0;
  const context = vm.createContext({
    window: {
      DASHBOARD_CONFIG: { timezone: "Asia/Tokyo", panelFetchTimeoutSeconds: 10 },
      HYDROPONICS_CONFIG: { summaryUrl: "/apps/hydroponics/api/summary", refreshSeconds: 60,
        fetchTimeoutSeconds: 10, idleReturnSeconds: 0, ...config },
      location: { assign: (url) => locations.push(url) },
    },
    document: {
      createElement: (tag) => new Element(tag), createDocumentFragment: () => new Element("fragment"),
      getElementById: (id) => id === "summary" ? summary : status,
      addEventListener: (event, callback) => events.set(event, callback),
    },
    AbortController, console: { error() {} },
    setTimeout: (callback, delay) => { const id = ++nextTimer; timers.set(id, { callback, delay }); return id; },
    clearTimeout: (id) => timers.delete(id), setInterval() {},
  });
  function load(file) {
    vm.runInContext(fs.readFileSync(path.resolve(__dirname, "..", file), "utf8"), context);
  }
  load("apps/hydroponics/static/summary.js");
  return { context, load, events, timers, summary, status, locations };
}

function sample() {
  return {
    measured_at: "2026-10-14T14:30:00+09:00", stale: false, overall: "system",
    actions: [{ text: "センサーを確認してください" }],
    items: [
      { metric: "water_temp", label: "液温", value: 20.56, unit: "℃", status: "ok" },
      { metric: "ec", label: "EC", value: 1.234, unit: "mS/cm", status: "ok" },
      { metric: "water_level", label: "水位", value: 99.9, unit: "cm", status: "stale",
        measured_at: "2026-10-14T11:20:00+09:00" },
    ],
  };
}

test("要約はECの桁を合わせ、欠測の古い値を表示しない", () => {
  const { context, summary } = browser();
  context.window.renderHydroponicsSummary(summary, sample());
  assert.match(summary.textContent, /20\.6 ℃/);
  assert.match(summary.textContent, /1\.23 mS\/cm/);
  assert.match(summary.textContent, /欠測（11:20より更新なし）/);
  assert.doesNotMatch(summary.textContent, /99\.9/);
});

test("未計測を正常として表示せず、危険な文字列もHTMLとして解釈しない", () => {
  const { context, summary } = browser();
  context.window.renderHydroponicsSummary(summary, { ...sample(), measured_at: null });
  assert.match(summary.textContent, /まだ計測データがありません/);
  assert.doesNotMatch(summary.textContent, /20\.6/);
  const data = sample();
  data.actions[0].text = '<img src=x onerror="alert(1)">';
  context.window.renderHydroponicsSummary(summary, data);
  assert.ok(summary.textContent.includes(data.actions[0].text));
});

test("パネルは要約し、専用画面は全項目と全作業を表示する", () => {
  const { context, summary } = browser();
  const data = sample();
  data.actions = ["作業A", "作業B", "作業C"].map((text) => ({ text }));
  data.items.push({ metric: "humidity", label: "湿度", value: 50, unit: "%", status: "none" });
  data.items.push({ metric: "light", label: "照度", value: 500, unit: "lx", status: "none" });
  context.window.renderHydroponicsSummary(summary, data, { maxActions: 2, maxItems: 4 });
  assert.match(summary.textContent, /他 1件/);
  assert.doesNotMatch(summary.textContent, /作業C|照度/);
  context.window.renderHydroponicsSummary(summary, data);
  assert.match(summary.textContent, /作業C/);
  assert.match(summary.textContent, /照度/);
});

test("応答形式が壊れていたら前回の表示を残す", () => {
  const { context, summary } = browser();
  context.window.renderHydroponicsSummary(summary, sample());
  const before = summary.textContent;
  assert.throws(() => context.window.renderHydroponicsSummary(summary, { overall: "unexpected" }));
  assert.equal(summary.textContent, before);
});

test("パネルはアプリのAPIを読み、障害中も前回の表示を残し、回復でエラーを消す", async () => {
  const { context, load, summary, status } = browser();
  load("apps/dashboard/static/dashboard.js");
  const panel = new Element();
  panel.dataset = { panelId: "hydroponics", apiUrl: "/apps/hydroponics/api/summary" };
  panel.querySelector = (selector) => selector === ".panel-status" ? status : summary;
  context.registerPanel("hydroponics", (body, data) => context.window.renderHydroponicsSummary(body, data));
  const urls = [];
  context.fetch = async (url) => { urls.push(url); return { ok: true, json: async () => sample() }; };
  await context.refreshPanel(panel);
  const before = summary.textContent;
  context.fetch = async () => ({ ok: false, status: 503 });
  await context.refreshPanel(panel);
  assert.equal(summary.textContent, before);
  assert.ok(panel.classes.has("is-error"));
  assert.match(status.textContent, /最終更新/);
  assert.equal(urls[0], "/apps/hydroponics/api/summary");
  context.fetch = async () => ({ ok: true, json: async () => sample() });
  await context.refreshPanel(panel);
  assert.equal(status.textContent, "");
  assert.ok(!panel.classes.has("is-error"));
});

test("従来のパネルAPIも利用でき、応答がない場合はタイムアウトで失敗する", async () => {
  const { context, load, timers, summary, status } = browser();
  load("apps/dashboard/static/dashboard.js");
  const panel = new Element();
  panel.dataset.panelId = "message";
  panel.querySelector = (selector) => selector === ".panel-status" ? status : summary;
  context.registerPanel("message", (body, data) => { body.textContent = data.text; });
  let requested;
  context.fetch = (url, { signal }) => new Promise((resolve, reject) => {
    requested = url;
    signal.addEventListener("abort", () => reject(new Error("aborted")));
  });
  const refresh = context.refreshPanel(panel);
  [...timers.values()].find((timer) => timer.delay === 10000).callback();
  await refresh;
  assert.equal(requested, "/api/panels/message");
  assert.match(status.textContent, /データを取得できません/);
});

test("専用画面も取得失敗中に前回の計測値を残す", async () => {
  const { context, load, summary, status } = browser();
  load("apps/hydroponics/static/app.js");
  context.fetch = async () => ({ ok: true, json: async () => sample() });
  await context.refreshSummary();
  const before = summary.textContent;
  context.fetch = async () => ({ ok: false, status: 503 });
  await context.refreshSummary();
  assert.equal(summary.textContent, before);
  assert.match(status.textContent, /最終更新/);
});

test("ダッシュボードからの遷移では操作で復帰タイマーを延長し、3分後に戻る", () => {
  const { context, load, events, timers, locations } = browser({ idleReturnSeconds: 180, dashboardUrl: "/" });
  context.fetch = async () => ({ ok: true, json: async () => sample() });
  load("apps/hydroponics/static/app.js");
  events.get("DOMContentLoaded")();
  const first = [...timers].find(([, timer]) => timer.delay === 180000);
  assert.ok(first);
  events.get("pointerdown")();
  assert.ok(!timers.has(first[0]));
  [...timers.values()].find((timer) => timer.delay === 180000).callback();
  assert.deepEqual(locations, ["/"]);
});

test("直接専用画面を開いた場合は、自動復帰を設定しない", () => {
  const { context, load, events, timers, locations } = browser({ dashboardUrl: "/" });
  context.fetch = async () => ({ ok: true, json: async () => sample() });
  load("apps/hydroponics/static/app.js");
  events.get("DOMContentLoaded")();
  assert.ok(![...timers.values()].some((timer) => timer.delay === 180000));
  assert.deepEqual(locations, []);
});
