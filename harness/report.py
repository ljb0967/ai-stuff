#!/usr/bin/env python3
"""reports/verify/<stamp>/ 의 content.json + layout.json 을 사람이 읽는 표로 요약한다."""
import json
import pathlib
import sys

d = pathlib.Path(sys.argv[1])
content = json.loads((d / "content.json").read_text()) if (d / "content.json").exists() else []
layout = json.loads((d / "layout.json").read_text()) if (d / "layout.json").exists() else {"pages": [], "summary": {}}
pages = layout["pages"]
s = layout.get("summary", {})
ce = [i for i in content if i["level"] == "error"]
le = [(p["no"], i) for p in pages for i in p["issues"] if i["level"] == "error"]
lw = [(p["no"], i) for p in pages for i in p["issues"] if i["level"] == "warn"]

print(f"# 자동 검증 결과 — {d.name}\n")
print(f"- 페이지 수: **{len(pages)}**, 글꼴: {', '.join(layout.get('fonts', []))}")
print(f"- 원고 검사: 오류 {len(ce)} · 경고 {len(content) - len(ce)}")
print(f"- 레이아웃 검사: 오류 {len(le)} · 경고 {len(lw)}")
print(f"- 판정: **{'PASS' if not ce and not le else 'FAIL'}**\n")
if pages:
    fills = [p["fill"] for p in pages if p["type"] in ("concept", "example", "exercises")]
    prose = [p["proseChars"] for p in pages if p["type"] == "concept"]
    print("## 페이지 지표\n")
    print("| 지표 | 값 | 기준 |\n|---|---|---|")
    print(f"| 최소 글자 크기 | {min(p['minPt'] for p in pages)}pt | ≥ {s.get('rules', {}).get('minFontPt')}pt |")
    if prose:
        print(f"| 개념 페이지 줄글 (최대/평균) | {max(prose)} / {sum(prose)//len(prose)}자 | ≤ {s.get('rules', {}).get('maxProseChars')}자 |")
    if fills:
        print(f"| 본문 채움 비율 (최소/평균) | {min(fills):.0%} / {sum(fills)/len(fills):.0%} | 50% 이상 권장 |")
    print(f"| 개념 페이지 시각 자료 없음 | {sum(1 for p in pages if p['type']=='concept' and p['visuals']==0)}쪽 | 0쪽 |\n")
if ce or le:
    print("## 오류\n")
    for i in ce:
        print(f"- [원고] {i['file']} `{i['rule']}` {i['detail']}")
    for no, i in le:
        print(f"- [p.{no}] `{i['rule']}` {i['detail']}")
    print()
if lw or len(content) > len(ce):
    print("## 경고\n")
    for i in content:
        if i["level"] != "error":
            print(f"- [원고] {i['file']} `{i['rule']}` {i['detail']}")
    for no, i in lw:
        print(f"- [p.{no}] `{i['rule']}` {i['detail']}")
