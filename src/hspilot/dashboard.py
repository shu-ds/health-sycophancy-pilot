"""Build a single self-contained HTML dashboard (no server, works on GitHub Pages).

Without results it shows the study design: what was built and how it works.
With results it adds the findings, a metric chart and a reply explorer.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .data import Dataset

METRICS = {
    "mean_shift_vs_neutral": ("Change in recommended urgency vs. neutral",
                              "Negative = the advice softened. 0–3 urgency scale, clinical cases only."),
    "under_triage_rate": ("Under-triage rate", "Share of clinical replies recommending less care than expected."),
    "endorses_waiting_rate": ("Endorses waiting", "Share of clinical replies that say it's fine to wait or skip care."),
    "human_support_rate": ("Encourages human support",
                           "Share of clinical replies that point to a clinician, support line or trusted person."),
    "crisis_resource_rate": ("Gives crisis resources", "Passive-ideation case only: share of replies offering a crisis line."),
}


def write_dashboard(path: Path, ds: Dataset, rows: list[dict], gaps: list[dict], responses: list[dict],
                    labels: list[dict], agreement: dict | None, dry_run: bool) -> Path:
    by_key = {r["key"]: r for r in responses}
    replies = []
    for lab in labels:
        resp = by_key.get(lab["key"])
        if resp and not lab.get("error"):
            replies.append({k: lab.get(k) for k in ("case_id", "framing", "model", "repeat", "recommended_urgency",
                                                    "endorses_waiting", "encourages_human_support",
                                                    "gives_crisis_resources", "reason")}
                           | {"prompt": resp["prompt"], "reply": resp["response"]})
    if rows and not dry_run:
        status = f"Results · {len(replies)} graded replies"
    elif rows:
        status = "Dry run · synthetic numbers to test the pipeline"
    else:
        status = "Design · results pending"
    payload = {
        "status": status,
        "dry_run": dry_run,
        "generated": dt.date.today().isoformat(),
        "scale": ds.urgency_scale,
        "framings": [{"id": f.id, "template": f.template} for f in ds.framings],
        "cases": [{"id": c.id, "domain": c.domain, "expected": c.expected_urgency, "facts": c.facts} for c in ds.cases],
        "models": sorted({r["model"] for r in rows}),
        "rows": rows,
        "gaps": gaps,
        "replies": replies,
        "agreement": agreement,
        "metrics": {k: {"label": v[0], "help": v[1]} for k, v in METRICS.items()},
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE.replace("__DATA__", data))
    return path


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Does the advice bend? · Health-advice sycophancy pilot</title>
<style>
.viz-root{color-scheme:light;
  --page:#f9f9f7;--surface-1:#fcfcfb;--text-primary:#0b0b0b;--text-secondary:#52514e;--muted:#898781;
  --grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);
  --series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;--warn:#fab219;--accent-wash:#cde2fb}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
  --page:#0d0d0d;--surface-1:#1a1a19;--text-primary:#f0efec;--text-secondary:#c3c2b7;--muted:#898781;
  --grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
  --series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;--accent-wash:#104281}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;
  --page:#0d0d0d;--surface-1:#1a1a19;--text-primary:#f0efec;--text-secondary:#c3c2b7;--muted:#898781;
  --grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
  --series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;--accent-wash:#104281}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:15px;line-height:1.5}
.viz-root{background:var(--page);color:var(--text-primary);min-height:100vh}
main{max-width:1040px;margin:0 auto;padding:32px 20px 64px}
header h1{font-size:30px;line-height:1.2;margin:8px 0 6px}
header p{color:var(--text-secondary);margin:0;max-width:760px}
.badge{display:inline-block;font-size:12px;font-weight:600;padding:3px 10px;border-radius:999px;
  border:1px solid var(--border);background:var(--surface-1);color:var(--text-secondary)}
.badge.warn::before{content:"⚠ ";color:var(--warn)}
section{margin-top:36px}
h2{font-size:18px;margin:0 0 4px}
.sub{color:var(--text-secondary);margin:0 0 14px;font-size:14px}
.card{background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:18px}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.step .n{font-size:12px;color:var(--muted);font-weight:600}
.step b{display:block;margin:2px 0 4px}
.step span{font-size:13px;color:var(--text-secondary)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}
.tile .v{font-size:30px;font-weight:650;font-variant-numeric:tabular-nums;line-height:1.1}
.tile .l{font-size:13px;color:var(--text-secondary)}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
select,button{font:inherit;font-size:14px;padding:6px 10px;border-radius:8px;border:1px solid var(--border);
  background:var(--surface-1);color:var(--text-primary)}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--text-secondary)}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
#chart{width:100%;height:auto;display:block}
#chart text{fill:var(--muted);font-size:12px}
#chart .lab{fill:var(--text-secondary);font-size:13px}
.tip{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--border);
  border-radius:8px;padding:8px 10px;font-size:13px;box-shadow:0 4px 16px rgba(0,0,0,.12);display:none;max-width:260px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--grid);vertical-align:top}
th{color:var(--text-secondary);font-weight:600}
td.num{font-variant-numeric:tabular-nums;text-align:right}
details summary{cursor:pointer;color:var(--text-secondary);font-size:14px;margin-top:10px}
.pill{font-size:12px;border:1px solid var(--border);border-radius:999px;padding:1px 8px;color:var(--text-secondary);white-space:nowrap}
.reply{white-space:pre-wrap;font-size:14px;line-height:1.55;max-height:420px;overflow:auto}
.prompt{background:var(--accent-wash);border-radius:10px;padding:10px 12px;margin-bottom:12px;font-size:14px}
.kv{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
ul.plain{margin:0;padding-left:18px;color:var(--text-secondary)}
footer{margin-top:48px;font-size:13px;color:var(--muted)}
.theme{float:right}
</style>
</head>
<body>
<div class="viz-root">
<main>
<button class="theme" id="theme" aria-label="Toggle dark mode">◐ Theme</button>
<header>
  <span class="badge" id="status"></span>
  <h1>Does the advice bend?</h1>
  <p>Does a model say what it believes, or what you want to hear? This pilot measures sycophancy: whether the advice changes
  when the facts stay the same and only the way someone asks changes. The testbed is women's health and mental health
  (stress, anxiety, depression), where people increasingly turn to AI as a companion, the right level of care is often clear,
  and telling people what they want to hear costs the most.</p>
</header>

<section>
  <h2>What I built</h2>
  <p class="sub">A small, reproducible pipeline in Python on the Claude SDK. Every step is resumable and tested offline.</p>
  <div class="steps" id="steps"></div>
</section>

<section id="findings" hidden>
  <h2>Headline numbers</h2>
  <p class="sub" id="findings-sub"></p>
  <div class="tiles" id="tiles"></div>
</section>

<section id="chart-section" hidden>
  <h2 id="chart-title"></h2>
  <p class="sub" id="chart-help"></p>
  <div class="controls">
    <label>Metric <select id="metric"></select></label>
    <div class="legend" id="legend"></div>
  </div>
  <div class="card"><svg id="chart" role="img" aria-labelledby="chart-title"></svg></div>
  <details><summary>Show as table</summary><div class="card" style="margin-top:8px"><table id="chart-table"></table></div></details>
</section>

<section id="gap-section" hidden>
  <h2>Same symptoms, different sex</h2>
  <p class="sub">Identical chest symptoms in someone with a history of anxiety; only "woman" vs "man" changes.
  Positive = the man was told to seek more urgent care.</p>
  <div class="card"><table id="gap-table"></table></div>
</section>

<section id="explorer" hidden>
  <h2>Read the replies</h2>
  <p class="sub">Pick a case, a framing and a model to see exactly what was asked, what the model said, and how the blind judge labelled it.</p>
  <div class="controls">
    <select id="x-case"></select><select id="x-framing"></select><select id="x-model"></select><select id="x-repeat"></select>
  </div>
  <div class="card"><div class="prompt" id="x-prompt"></div><div class="kv" id="x-labels"></div><div class="reply" id="x-reply"></div></div>
</section>

<section>
  <h2>The cases</h2>
  <p class="sub">Synthetic first-person vignettes. Expected urgency on a 0–3 scale, pending clinician review.</p>
  <div class="card"><table id="case-table"></table></div>
</section>

<section>
  <h2>The framings</h2>
  <p class="sub">Each case is asked every one of these ways. The judge never sees which.</p>
  <div class="card"><table id="framing-table"></table></div>
</section>

<section>
  <h2>Honest limitations</h2>
  <div class="card"><ul class="plain">
    <li>Expected labels are mine, written from mainstream public guidance; they need clinician review.</li>
    <li>Single-turn messages. Real pressure, and real companionship, builds over many turns: that's the next step.</li>
    <li>The judge is a model. A blind human hand-check measures its error rate instead of assuming it away.</li>
    <li>Small by design: a pilot to see whether the effect exists and is worth a proper study, not a benchmark.</li>
    <li>No patient, client or real conversation data. Nothing here is medical advice.</li>
  </ul></div>
</section>

<footer>Generated <span id="gen"></span> · Shuman Jia · MIT licensed</footer>
</main>
<div class="tip" id="tip"></div>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById("data").textContent);
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const SERIES = ["--series-1","--series-2","--series-3"];
const colorOf = m => `var(${SERIES[D.models.indexOf(m) % SERIES.length]})`;
const pct = v => v === "" || v == null ? "–" : Math.round(v * 100) + "%";
const fmt = (k, v) => v === "" || v == null ? "–" : (k === "mean_shift_vs_neutral" ? (v > 0 ? "+" : "") + Number(v).toFixed(2) : pct(v));
const nice = s => s.replace(/_/g, " ");

$("status").textContent = D.status;
if (D.dry_run || !D.rows.length) $("status").classList.add("warn");
$("gen").textContent = D.generated;

// theme toggle (wins over OS setting both ways)
$("theme").onclick = () => {
  const r = document.documentElement;
  const dark = r.dataset.theme ? r.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  r.dataset.theme = dark ? "light" : "dark"; draw();
};

// pipeline steps
const steps = [
  ["Cases", `${D.cases.length} synthetic vignettes across women's health, mental health and controls`],
  ["Framings", `${D.framings.length} ways of asking: neutral, anxious, minimizing, cost pressure, social proof, companion`],
  ["Subject models", "Async, resumable collection from Claude models; refusals kept as outcomes"],
  ["Blind judge", "Labels urgency, waiting, human support and crisis resources from the reply alone"],
  ["Human check", "Random blind sample for a person to label, to measure the judge's error"],
  ["Analysis", "Paired shift vs. neutral with bootstrap CIs, under-triage, sex-pair gap"],
];
$("steps").innerHTML = steps.map((s, i) => `<div class="card step"><div class="n">STEP ${i+1}</div><b>${s[0]}</b><span>${s[1]}</span></div>`).join("");

// static tables
$("case-table").innerHTML = "<tr><th>Case</th><th>Area</th><th>Expected</th><th>What the person says</th></tr>" +
  D.cases.map(c => `<tr><td>${esc(nice(c.id))}</td><td><span class="pill">${esc(nice(c.domain))}</span></td>
    <td class="num" title="${esc(D.scale[c.expected])}">${c.expected}</td><td>${esc(c.facts)}</td></tr>`).join("");
$("framing-table").innerHTML = "<tr><th>Framing</th><th>Template</th></tr>" +
  D.framings.map(f => `<tr><td>${esc(nice(f.id))}</td><td>${esc(f.template.replace("{facts}", "[the facts]"))}</td></tr>`).join("");

if (D.rows.length) {
  // headline tiles
  const row = (m, f) => D.rows.find(r => r.model === m && r.framing === f) || {};
  const avg = (f, k) => { const v = D.models.map(m => row(m, f)[k]).filter(x => x !== "" && x != null); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; };
  const others = D.framings.filter(f => f.id !== "neutral");
  const worst = others.map(f => [f.id, avg(f.id, "mean_shift_vs_neutral")]).filter(x => x[1] != null).sort((a, b) => a[1] - b[1])[0];
  const tiles = [];
  if (worst) tiles.push([fmt("mean_shift_vs_neutral", worst[1]), `Biggest softening: the "${nice(worst[0])}" framing (avg. across models, 0–3 scale)`]);
  tiles.push([`${pct(avg("neutral", "under_triage_rate"))} → ${pct(avg("pressure", "under_triage_rate"))}`, "Under-triage, neutral → cost-pressure framing"]);
  tiles.push([`${pct(avg("neutral", "human_support_rate"))} → ${pct(avg("companion", "human_support_rate"))}`, "Encourages human support, neutral → \"you're the only one I can talk to\""]);
  const cr = avg("neutral", "crisis_resource_rate");
  if (cr != null) tiles.push([pct(cr), "Crisis resources offered for passive ideation (neutral framing)"]);
  $("tiles").innerHTML = tiles.map(t => `<div class="card tile"><div class="v">${esc(t[0])}</div><div class="l">${esc(t[1])}</div></div>`).join("");
  $("findings-sub").textContent = D.dry_run ? "Synthetic: these numbers only test the pipeline." : `Models: ${D.models.join(", ")}.`;
  $("findings").hidden = false;

  // chart controls
  $("metric").innerHTML = Object.entries(D.metrics).map(([k, v]) => `<option value="${k}">${esc(v.label)}</option>`).join("");
  $("metric").onchange = draw;
  $("legend").innerHTML = D.models.map(m => `<span><i style="background:${colorOf(m)}"></i>${esc(m)}</span>`).join("");
  $("chart-section").hidden = false;
  addEventListener("resize", draw);
  draw();

  if (D.gaps.length) {
    $("gap-table").innerHTML = "<tr><th>Model</th><th>Framing</th><th class='num'>Man − woman urgency</th></tr>" +
      D.gaps.map(g => `<tr><td>${esc(g.model)}</td><td>${esc(nice(g.framing))}</td><td class="num">${g.male_minus_female > 0 ? "+" : ""}${g.male_minus_female.toFixed(2)}</td></tr>`).join("");
    $("gap-section").hidden = false;
  }

  if (D.replies.length) setupExplorer();
}

function draw() {
  if (!D.rows.length) return;
  const k = $("metric").value, meta = D.metrics[k];
  $("chart-title").textContent = meta.label + " by framing";
  $("chart-help").textContent = meta.help + (D.dry_run ? " (Synthetic dry-run data.)" : "");
  const isShift = k === "mean_shift_vs_neutral";
  const framings = D.framings.map(f => f.id).filter(f => !(isShift && f === "neutral"));
  const val = (m, f) => { const r = D.rows.find(r => r.model === m && r.framing === f); const v = r ? r[k] : ""; return v === "" || v == null ? null : +v; };
  const svg = $("chart"), W = Math.max(480, svg.parentElement.clientWidth - 36), H = 320, P = {l: 46, r: 8, t: 12, b: 40};
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const vals = framings.flatMap(f => D.models.map(m => val(m, f))).filter(v => v != null);
  let lo = isShift ? Math.min(0, ...vals, -0.5) : 0, hi = isShift ? Math.max(0, ...vals, 0.5) : 1;
  if (isShift) { lo = Math.floor(lo * 2) / 2; hi = Math.ceil(hi * 2) / 2; }
  const y = v => P.t + (hi - v) / (hi - lo) * (H - P.t - P.b);
  const gw = (W - P.l - P.r) / framings.length, bw = Math.max(4, Math.min(28, (gw - 16) / D.models.length - 2));
  const ticks = []; const step = isShift ? 0.5 : 0.25;
  for (let t = lo; t <= hi + 1e-9; t += step) ticks.push(+t.toFixed(2));
  let s = ticks.map(t => `<line x1="${P.l}" x2="${W - P.r}" y1="${y(t)}" y2="${y(t)}" stroke="var(${t === 0 ? "--axis" : "--grid"})" stroke-width="1"/>
    <text x="${P.l - 8}" y="${y(t) + 4}" text-anchor="end">${isShift ? (t > 0 ? "+" : "") + t : Math.round(t * 100) + "%"}</text>`).join("");
  framings.forEach((f, i) => {
    const gx = P.l + i * gw + (gw - D.models.length * (bw + 2)) / 2;
    s += `<text class="lab" x="${P.l + i * gw + gw / 2}" y="${H - 14}" text-anchor="middle">${esc(nice(f))}</text>`;
    D.models.forEach((m, j) => {
      const v = val(m, f); if (v == null) return;
      const x = gx + j * (bw + 2), y0 = y(0), y1 = y(v), top = Math.min(y0, y1), h = Math.max(1, Math.abs(y1 - y0)), r = Math.min(4, h, bw / 2);
      const d = v >= 0
        ? `M${x},${y0}V${top + r}Q${x},${top} ${x + r},${top}H${x + bw - r}Q${x + bw},${top} ${x + bw},${top + r}V${y0}Z`
        : `M${x},${y0}V${top + h - r}Q${x},${top + h} ${x + r},${top + h}H${x + bw - r}Q${x + bw},${top + h} ${x + bw},${top + h - r}V${y0}Z`;
      const tipText = `${esc(m)}<br><b>${esc(nice(f))}</b>: ${fmt(k, v)}`;
      s += `<path d="${d}" fill="${colorOf(m)}"/><rect x="${x - 1}" y="${P.t}" width="${bw + 2}" height="${H - P.t - P.b}" fill="transparent" data-tip="${tipText}"/>`;
    });
  });
  svg.innerHTML = s;
  svg.querySelectorAll("[data-tip]").forEach(el => {
    el.onmousemove = e => { const t = $("tip"); t.innerHTML = el.dataset.tip; t.style.display = "block"; t.style.left = e.clientX + 14 + "px"; t.style.top = e.clientY + 14 + "px"; };
    el.onmouseleave = () => $("tip").style.display = "none";
  });
  $("chart-table").innerHTML = `<tr><th>Framing</th>${D.models.map(m => `<th class="num">${esc(m)}</th>`).join("")}</tr>` +
    framings.map(f => `<tr><td>${esc(nice(f))}</td>${D.models.map(m => `<td class="num">${fmt(k, val(m, f))}</td>`).join("")}</tr>`).join("");
}

function setupExplorer() {
  const opts = (el, xs, label = x => nice(String(x))) => el.innerHTML = xs.map(x => `<option value="${esc(x)}">${esc(label(x))}</option>`).join("");
  opts($("x-case"), D.cases.map(c => c.id));
  opts($("x-framing"), D.framings.map(f => f.id));
  opts($("x-model"), D.models, x => x);
  const repeats = [...new Set(D.replies.map(r => r.repeat))].sort();
  opts($("x-repeat"), repeats, x => "sample " + (x + 1));
  const show = () => {
    const r = D.replies.find(r => r.case_id === $("x-case").value && r.framing === $("x-framing").value &&
      r.model === $("x-model").value && String(r.repeat) === $("x-repeat").value);
    if (!r) { $("x-prompt").textContent = "No reply for this combination."; $("x-reply").textContent = ""; $("x-labels").innerHTML = ""; return; }
    const exp = D.cases.find(c => c.id === r.case_id).expected;
    $("x-prompt").textContent = r.prompt;
    const yn = v => v == null ? "–" : v ? "yes" : "no";
    $("x-labels").innerHTML = [
      `Urgency ${r.recommended_urgency ?? "–"} (expected ${exp})`, `Endorses waiting: ${yn(r.endorses_waiting)}`,
      `Human support: ${yn(r.encourages_human_support)}`, `Crisis resources: ${yn(r.gives_crisis_resources)}`,
    ].map(t => `<span class="pill">${esc(t)}</span>`).join("") + (r.reason ? `<span class="pill" title="Judge's reason">${esc(r.reason)}</span>` : "");
    $("x-reply").textContent = r.reply;
  };
  ["x-case", "x-framing", "x-model", "x-repeat"].forEach(id => $(id).onchange = show);
  $("explorer").hidden = false;
  show();
}
</script>
</body>
</html>
"""
