#!/usr/bin/env python3
"""원고(YAML) 내용 검사 — 렌더링 전에 잡을 수 있는 문제를 찾는다.

  python harness/check.py                 # textbook/src/*.yaml 전체
  python harness/check.py --src textbook/src/03_unit02.yaml

검사 항목
  answer      : 확인 문제·유제마다 정답(answer)이 있는가
  goals       : 단원 도입 페이지에 학습 목표가 3개 있는가
  structure   : 단원에 도입·개념·예제·확인 문제·마무리 페이지가 모두 있는가
  warn-box    : 단원마다 ⚠ 주의(warn) 상자가 1개 이상 있는가 (윤리 분산 원칙)
  numbering   : 확인 문제 번호가 1부터 빠짐없이 이어지는가
  terms       : 영어 약어(LLM, MCP 등)가 단원 용어집이나 곁단 용어 메모에 풀이되어 있는가
  product     : 본문에 특정 제품명이 들어갔는가 (허용 목록 밖이면 경고)
  figure-no   : 그림·표 번호가 단원 번호와 맞는가
  persona     : 등장인물 이름이 기획서의 4명 중 하나인가
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build import ROOT, SRC, load_doc, norm_block  # noqa: E402

PRODUCTS = ["ChatGPT", "챗GPT", "Gemini", "제미나이", "Claude", "클로드", "Copilot", "코파일럿", "Manus", "뤼튼", "클로바"]
# 역사적 사건·출처 있는 통계에서만 허용 (revision_round1 M11)
PRODUCT_OK_CONTEXT = ["Mata", "Avianca", "와이즈앱", "MAU", "판례", "부록"]
ACRONYMS = ["AI", "LLM", "MCP", "API", "OX", "SNS", "PDF", "URL", "MFA", "OTP"]
ACRONYM_SELF_EVIDENT = {"AI", "OX", "SNS", "PDF", "URL"}  # 1단원에서 풀이하거나 일상어
PERSONAS = ["김정숙", "박영호", "이수진", "최민호"]
REQUIRED_TYPES = ["opener", "concept", "example", "exercises", "summary"]


def walk_text(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from walk_text(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_text(v)


def check_doc(path: pathlib.Path, glossary_all: set[str]) -> list[dict]:
    doc = load_doc(path)
    out = []
    unit = doc.get("unit")

    def add(level, rule, detail):
        out.append({"file": path.name, "unit": unit, "level": level, "rule": rule, "detail": detail})

    pages = doc.get("pages", [])
    types = [p.get("type", "concept") for p in pages]
    if unit:
        for t in REQUIRED_TYPES:
            if t == "example" and ("practice" in types or "project" in types):  # 따라 해 보기·프로젝트(모범 예시) 페이지도 인정
                continue
            if t not in types:
                add("error", "structure", f"'{t}' 페이지가 없음")
        op = next((p for p in pages if p.get("type") == "opener"), None)
        if op and len(op.get("goals", [])) != 3:
            add("error", "goals", f"학습 목표 {len(op.get('goals', []))}개 (3개여야 함)")

    ex_nos, warn_count = [], 0
    term_titles = set(g["term"] for g in doc.get("glossary", []))
    for pi, pg in enumerate(pages, 1):
        blocks = [norm_block(b) for b in pg.get("blocks", [])] + [norm_block(b) for b in pg.get("side", [])]
        for b in blocks:
            if b["type"] == "note" and b.get("kind", "term") == "term" and b.get("title"):
                term_titles.add(b["title"])
            if b["type"] == "warn" or (b["type"] == "note" and b.get("kind") == "warn"):
                warn_count += 1
            if b["type"] == "exercises":
                for it in b["items"]:
                    ex_nos.append(it.get("no"))
                    if it.get("kind") == "mc" and len(it.get("choices") or []) not in (4, 5):
                        add("error", "choices", f"p{pi} 문제 {it.get('no')} 선택지 {len(it.get('choices') or [])}개 (쉼표로 쪼개졌는지 확인)")
                    if not it.get("answer"):
                        add("error", "answer", f"p{pi} 확인 문제 {it.get('no')} 정답 없음")
            if b["type"] == "table" and b.get("head"):
                for r in b.get("rows", []):
                    if len(r) != len(b["head"]):
                        add("error", "table-cols", f"p{pi} 표 '{b.get('label', '')}' 행 칸 수 {len(r)} ≠ 머리 {len(b['head'])}: {str(r[0])[:20]}")
            if b["type"] == "exercises":
                for it in b["items"]:
                    for pr in it.get("pairs") or []:
                        if len(pr) != 2:
                            add("error", "pair", f"p{pi} 문제 {it.get('no')} 짝짓기 항목 칸 수 {len(pr)}: {pr}")
            if b["type"] == "similar" and not b.get("answer"):
                add("error", "answer", f"p{pi} 유제 {b.get('no')} 정답 없음")
            for key in ("label",):
                lab = b.get(key) or (b.get("figure") or {}).get("label") if isinstance(b.get("figure"), dict) else b.get(key)
                if unit and isinstance(lab, str):
                    m = re.search(r"(\d+)-\d+", lab)
                    if m and int(m.group(1)) != unit:
                        add("warn", "figure-no", f"p{pi} '{lab}' 번호가 {unit}단원과 다름")
    if unit and warn_count == 0:
        add("error", "warn-box", "주의(warn) 상자가 하나도 없음")
    if ex_nos and ex_nos != list(range(1, len(ex_nos) + 1)):
        add("error", "numbering", f"확인 문제 번호 {ex_nos}")

    # 흐름식 매핑 { a: x, b: y } 안의 쉼표 때문에 문장이 잘려 '값 없는 키'가 생긴 경우를 잡는다
    def find_split(obj, path="") :
        if isinstance(obj, dict):
            for k, v in obj.items():
                if v is None and isinstance(k, str) and (" " in k or any("가" <= ch <= "힣" for ch in k)):
                    add("error", "yaml-split", f"{path} 쉼표로 잘린 문장 의심: '{k[:30]}' (따옴표로 감싸세요)")
                find_split(v, f"{path}/{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                find_split(v, f"{path}[{i}]")
    find_split(doc)

    text = "\n".join(walk_text(doc))
    for ac in ACRONYMS:
        if ac in ACRONYM_SELF_EVIDENT:
            continue
        if re.search(rf"(?<![A-Za-z]){ac}(?![A-Za-z])", text):
            if not any(ac in t for t in term_titles | glossary_all):
                add("warn", "terms", f"약어 '{ac}' 풀이(용어 메모·용어집) 없음")
    for prod in ([] if path.name.startswith("99_") else PRODUCTS):  # 부록의 서비스 현황표는 예외
        for m in re.finditer(re.escape(prod), text):
            ctx = text[max(0, m.start() - 80): m.end() + 80]
            if not any(c in ctx for c in PRODUCT_OK_CONTEXT):
                add("warn", "product", f"제품명 '{prod}' 사용: …{ctx[60:140].strip()}…")
                break
    surnames = set("김이박최정강조윤장임한오서신권황안송류전홍고문양손배백허유남심노하곽성차주우구민진나지엄채원천방공현함변염여추도소석선설마길연위표명기반왕금옥육인맹제모탁국어은편용예봉경사부")
    for name in re.findall(r"([가-힣]{3}) ?(?:님|사장님|주무관|씨)", text):
        if name[0] in surnames and name not in PERSONAS and name not in ("선생님", "손주가", "손님이"):
            add("warn", "persona", f"등장인물 목록에 없는 이름 '{name}'")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", nargs="*")
    ap.add_argument("--report")
    a = ap.parse_args()
    files = [pathlib.Path(s) for s in a.src] if a.src else sorted(SRC.glob("*.yaml"))
    glossary_all = set()
    for f in sorted(SRC.glob("*.yaml")):
        glossary_all |= {g["term"] for g in (load_doc(f).get("glossary") or [])}
    issues = [i for f in files for i in check_doc(f, glossary_all)]
    errs = [i for i in issues if i["level"] == "error"]
    for i in issues:
        print(f"  {i['level'].upper():5} {i['file']} [{i['rule']}] {i['detail']}")
    print(f"content check: files={len(files)} errors={len(errs)} warnings={len(issues) - len(errs)}")
    if a.report:
        pathlib.Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.report).write_text(json.dumps(issues, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
