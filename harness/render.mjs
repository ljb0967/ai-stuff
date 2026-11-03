#!/usr/bin/env node
// 교안 HTML → PDF / PNG + 레이아웃 자동 검사
//   node harness/render.mjs --html dist/book.html --pdf dist/book.pdf --png dist/png --report reports/verify/layout.json
//   옵션: --scale 1.5 (PNG 배율), --pages 1-6,9 (PNG로 뽑을 페이지)
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright"); // 전역 설치본(NODE_PATH) 사용
import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => (a.startsWith("--") ? [...acc, [a.slice(2), arr[i + 1]]] : acc), [])
);
if (!args.html) { console.error("--html 필요"); process.exit(2); }

// 검사 기준 (docs/plan/curriculum.md 5장, revision_round1.md M7)
const RULES = {
  minFontPt: 10.5,          // 캡션·주석 최소
  bodyFontPt: 13,           // 본문
  maxProseChars: 800,       // 페이지당 줄글
  warnSentenceChars: 100,   // 문장 길이 경고
  minVisualsConcept: 1,     // 개념 페이지 시각 자료
};
const PT = 96 / 72;

function parsePages(spec, total) {
  if (!spec) return [...Array(total).keys()].map((i) => i + 1);
  const out = [];
  for (const part of spec.split(",")) {
    const [a, b] = part.split("-").map(Number);
    for (let i = a; i <= (b || a); i++) out.push(i);
  }
  return out.filter((n) => n >= 1 && n <= total);
}

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 900, height: 1200 }, deviceScaleFactor: Number(args.scale || 1) });
const page = await ctx.newPage();
await page.goto(url.pathToFileURL(path.resolve(args.html)).href, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);
await page.emulateMedia({ media: "print" });

const report = await page.evaluate(({ RULES, PT }) => {
  const pages = [...document.querySelectorAll(".page")];
  const fontsOk = [...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family);
  const res = pages.map((pg) => {
    const no = Number(pg.dataset.page);
    const type = pg.dataset.type;
    const body = pg.querySelector(".body");
    const br = body.getBoundingClientRect();
    const pr = pg.getBoundingClientRect();
    const issues = [];
    // 1) 넘침: 본문 영역 밖으로 나간 요소
    let maxBottom = br.top;
    for (const el of body.querySelectorAll(".main > *, .main > * *, .side > *, .side > * *")) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      if (getComputedStyle(el).position === "absolute") continue;
      maxBottom = Math.max(maxBottom, r.bottom);
      if (r.right > pr.right - 2 || r.left < pr.left + 2) {
        issues.push({ level: "error", rule: "overflow-x", detail: `${el.className || el.tagName} 가로 넘침` });
        break;
      }
    }
    const overflowPx = maxBottom - br.bottom;
    if (overflowPx > 1) issues.push({ level: "error", rule: "overflow", detail: `본문 영역을 ${(overflowPx / 3.78).toFixed(1)}mm 넘침` });
    const fill = (Math.min(maxBottom, br.bottom) - br.top) / br.height;
    // 2) 최소 글자 크기
    let minPt = 99, minEl = "";
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const t = walker.currentNode;
      if (!t.textContent.trim()) continue;
      const el = t.parentElement;
      const cs = getComputedStyle(el);
      if (cs.color === "transparent" || cs.visibility === "hidden" || cs.display === "none") continue;
      let px = parseFloat(cs.fontSize);
      if (el.closest("svg")) {
        const svg = el.closest("svg");
        const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
        px = px * scale;
      }
      const pt = px / PT;
      if (pt < minPt) { minPt = pt; minEl = (el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className) || el.tagName; }
    }
    if (minPt < RULES.minFontPt - 0.05) issues.push({ level: "error", rule: "min-font", detail: `${minPt.toFixed(1)}pt (${minEl}) < ${RULES.minFontPt}pt` });
    // 3) 줄글 분량·문장 길이 (박스·표 제외한 본문 단락)
    const prose = [...pg.querySelectorAll(".main > .para, .main > .lead, .main > .list li")].map((e) => e.textContent.trim());
    const proseChars = prose.join("").length;
    if (proseChars > RULES.maxProseChars) issues.push({ level: "error", rule: "density", detail: `줄글 ${proseChars}자 > ${RULES.maxProseChars}자` });
    const allText = [...pg.querySelectorAll(".para, .lead, .concept-body, .callout-body, .ex-q, .exq-q, .note-body")].map((e) => e.innerText).join("\n");
    const longS = allText.split(/\n|(?<=[.?!])\s+/).map((s) => s.trim()).filter((s) => s.length > RULES.warnSentenceChars);
    for (const s of longS) issues.push({ level: "warn", rule: "long-sentence", detail: `${s.length}자: ${s.slice(0, 40)}…` });
    // 4) 시각 자료
    const visuals = pg.querySelectorAll(".fig, .tbl, .win, .approval").length;
    if (type === "concept" && visuals < RULES.minVisualsConcept) issues.push({ level: "error", rule: "visual", detail: "개념 페이지에 도표·그림·표 없음" });
    // 5) 미정의 블록
    if (pg.querySelector(".unknown-block")) issues.push({ level: "error", rule: "unknown-block", detail: pg.querySelector(".unknown-block").textContent });
    // 6) 너무 빈 페이지
    if (["concept", "example", "exercises"].includes(type) && fill < 0.6) issues.push({ level: "warn", rule: "sparse", detail: `채움 ${(fill * 100).toFixed(0)}%` });
    return { no, type, unit: pg.dataset.unit || null, fill: +fill.toFixed(2), proseChars, visuals, minPt: +minPt.toFixed(1), issues };
  });
  return { fonts: [...new Set(fontsOk)], pages: res };
}, { RULES, PT });

const errors = report.pages.flatMap((p) => p.issues.filter((i) => i.level === "error").map((i) => ({ page: p.no, ...i })));
const warns = report.pages.flatMap((p) => p.issues.filter((i) => i.level === "warn").map((i) => ({ page: p.no, ...i })));
report.summary = { pages: report.pages.length, errors: errors.length, warnings: warns.length, rules: RULES };

if (args.pdf) {
  await page.pdf({ path: args.pdf, preferCSSPageSize: true, printBackground: true });
}
if (args.png) {
  fs.mkdirSync(args.png, { recursive: true });
  const els = await page.$$(".page");
  for (const n of parsePages(args.pages, els.length)) {
    await els[n - 1].screenshot({ path: path.join(args.png, `page-${String(n).padStart(3, "0")}.png`) });
  }
}
if (args.report) {
  fs.mkdirSync(path.dirname(args.report), { recursive: true });
  fs.writeFileSync(args.report, JSON.stringify(report, null, 1));
}
await browser.close();

console.log(`pages=${report.pages.length} errors=${errors.length} warnings=${warns.length} fonts=${report.fonts.join(",")}`);
for (const e of errors) console.log(`  ERROR p.${e.page} [${e.rule}] ${e.detail}`);
for (const w of warns.slice(0, 30)) console.log(`  warn  p.${w.page} [${w.rule}] ${w.detail}`);
process.exit(errors.length ? 1 : 0);
