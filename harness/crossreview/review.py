#!/usr/bin/env python3
"""외부 LLM 교차 검토 하네스.

교안 산출물(기획 문서, 디자인 시안, 단원 PDF 페이지)을 외부 LLM(GPT, Gemini)에게
같은 채점 기준(rubric)으로 검토받고, 결과를 reports/crossreview/ 에 남긴다.

사용 예:
  python harness/crossreview/review.py --rubric plan  --files docs/plan/curriculum.md docs/plan/units/*.md
  python harness/crossreview/review.py --rubric pages --pdf dist/ai-literacy-workbook.pdf --pages 7-12
  python harness/crossreview/review.py --rubric design --images design/candidates/*.png
  python harness/crossreview/review.py --rubric pages --pdf dist/x.pdf --provider packet   # 수동 검토용 묶음만 생성

공급자(provider):
  openai : OPENAI_API_KEY 필요 (모델: CROSSREVIEW_OPENAI_MODEL, 기본 gpt-5)
  gemini : GEMINI_API_KEY 또는 GOOGLE_API_KEY 필요 (모델: CROSSREVIEW_GEMINI_MODEL, 기본 gemini-2.5-pro)
  auto   : 키가 있는 공급자를 모두 사용 (기본값)
  packet : API를 호출하지 않고, 프롬프트와 첨부 이미지를 폴더로 묶어 둔다.
           ChatGPT/Gemini 웹 화면에 그대로 붙여 넣어 수동 교차 검토할 때 쓴다.

키가 하나도 없으면 결과를 지어내지 않고 SKIPPED 기록과 packet만 남긴 뒤 종료 코드 3을 돌려준다.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import glob
import json
import os
import pathlib
import re
import shutil
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUBRIC_DIR = pathlib.Path(__file__).resolve().parent / "rubrics"
OUT_DIR = ROOT / "reports" / "crossreview"

SYSTEM_PROMPT = (
    "당신은 성인 대상 디지털·AI 리터러시 교재를 검토하는 독립 검수자입니다. "
    "교재 제작자와 다른 회사의 모델로서, 제작자가 놓친 문제를 찾는 것이 임무입니다. "
    "칭찬보다 결함 발견에 집중하고, 근거 없는 추측은 하지 마세요. "
    "반드시 지정된 JSON 형식으로만 답하세요."
)

JSON_SPEC = """
출력 형식(JSON 하나만 출력):
{
  "overall_score": 0~100 정수,
  "verdict": "pass" | "revise" | "fail",
  "summary": "한두 문장 총평",
  "findings": [
    {"severity": "critical|major|minor",
     "category": "정확성|난이도|구성|안전·윤리|디자인|문체|기타",
     "location": "파일명/페이지/단원 등 위치",
     "issue": "무엇이 문제인가",
     "suggestion": "어떻게 고치면 되는가"}
  ]
}
"""


# ---------------------------------------------------------------- inputs

def load_rubric(name: str) -> str:
    path = RUBRIC_DIR / f"{name}.md"
    if not path.exists():
        sys.exit(f"rubric not found: {path}")
    return path.read_text(encoding="utf-8")


def expand(patterns: list[str]) -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for p in patterns or []:
        hits = sorted(glob.glob(p)) or [p]
        out += [pathlib.Path(h) for h in hits]
    return out


def parse_pages(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(1, total + 1))
    pages: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages += list(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= total]


def pdf_to_inputs(pdf: pathlib.Path, spec: str | None, workdir: pathlib.Path):
    """PDF 페이지를 PNG(시각 검토용)와 텍스트(내용 검토용)로 바꾼다."""
    import pypdfium2 as pdfium  # 설치되어 있음

    doc = pdfium.PdfDocument(str(pdf))
    images, texts = [], []
    for no in parse_pages(spec, len(doc)):
        page = doc[no - 1]
        img = page.render(scale=1.4).to_pil()
        path = workdir / f"page-{no:03d}.png"
        img.save(path)
        images.append(path)
        texts.append(f"--- p.{no} ---\n" + page.get_textpage().get_text_range())
    return images, "\n".join(texts)


def build_prompt(rubric: str, files: list[pathlib.Path], extra_text: str) -> str:
    parts = [rubric.strip(), JSON_SPEC.strip(), "\n# 검토 대상"]
    for f in files:
        parts.append(f"\n## 파일: {f.relative_to(ROOT) if f.is_absolute() else f}\n")
        parts.append(f.read_text(encoding="utf-8"))
    if extra_text:
        parts.append("\n## 페이지 추출 텍스트\n" + extra_text)
    return "\n".join(parts)


# ---------------------------------------------------------------- providers

def _post(url: str, payload: dict, headers: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:  # 오류 본문을 그대로 남긴다
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:800]}") from e


def _b64(path: pathlib.Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def call_openai(prompt: str, images: list[pathlib.Path]) -> tuple[str, str]:
    model = os.environ.get("CROSSREVIEW_OPENAI_MODEL", "gpt-5")
    content = [{"type": "text", "text": prompt}]
    for img in images:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64(img)}"}})
    data = _post(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
        },
        {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
    )
    return model, data["choices"][0]["message"]["content"]


def call_gemini(prompt: str, images: list[pathlib.Path]) -> tuple[str, str]:
    model = os.environ.get("CROSSREVIEW_GEMINI_MODEL", "gemini-2.5-pro")
    key = os.environ.get("GEMINI_API_KEY") or os.environ["GOOGLE_API_KEY"]
    parts = [{"text": prompt}] + [{"inline_data": {"mime_type": "image/png", "data": _b64(i)}} for i in images]
    data = _post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseMimeType": "application/json"},
        },
        {},
    )
    return model, data["candidates"][0]["content"]["parts"][0]["text"]


PROVIDERS = {
    "openai": (lambda: bool(os.environ.get("OPENAI_API_KEY")), call_openai),
    "gemini": (lambda: bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")), call_gemini),
}


# ---------------------------------------------------------------- reporting

def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def to_markdown(result: dict, provider: str, model: str, label: str) -> str:
    lines = [
        f"# 교차 검토 결과 — {label}",
        "",
        f"- 검토자: **{provider}** (`{model}`)",
        f"- 일시: {dt.datetime.now().isoformat(timespec='minutes')}",
        f"- 점수: **{result.get('overall_score')}** / 판정: **{result.get('verdict')}**",
        f"- 총평: {result.get('summary', '')}",
        "",
        "| 심각도 | 분류 | 위치 | 문제 | 제안 |",
        "|---|---|---|---|---|",
    ]
    order = {"critical": 0, "major": 1, "minor": 2}
    for f in sorted(result.get("findings", []), key=lambda x: order.get(x.get("severity"), 9)):
        cells = [f.get(k, "").replace("|", "\\|").replace("\n", " ") for k in
                 ("severity", "category", "location", "issue", "suggestion")]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_packet(dirpath: pathlib.Path, prompt: str, images: list[pathlib.Path]) -> None:
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "PROMPT.md").write_text(
        "<!-- ChatGPT/Gemini 웹에 아래 전체를 붙여 넣고, 같은 폴더의 이미지를 함께 첨부하세요. -->\n\n"
        + SYSTEM_PROMPT + "\n\n" + prompt,
        encoding="utf-8",
    )
    for img in images:
        shutil.copy(img, dirpath / img.name)


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rubric", required=True, help="rubrics/<name>.md (plan|design|pages)")
    ap.add_argument("--files", nargs="*", default=[], help="검토할 텍스트/마크다운 파일")
    ap.add_argument("--images", nargs="*", default=[], help="검토할 이미지(PNG)")
    ap.add_argument("--pdf", help="검토할 PDF")
    ap.add_argument("--pages", help="PDF 페이지 범위, 예: 1-6,9")
    ap.add_argument("--provider", default="auto", choices=["auto", "openai", "gemini", "packet"])
    ap.add_argument("--label", default=None, help="보고서 이름")
    args = ap.parse_args()

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    label = args.label or f"{args.rubric}-{stamp}"
    run_dir = OUT_DIR / label
    work = run_dir / "inputs"
    work.mkdir(parents=True, exist_ok=True)

    files = expand(args.files)
    images = expand(args.images)
    extra = ""
    if args.pdf:
        pimgs, extra = pdf_to_inputs(pathlib.Path(args.pdf), args.pages, work)
        images += pimgs
    prompt = build_prompt(load_rubric(args.rubric), files, extra)

    # 언제나 수동 검토용 묶음을 남긴다 (재현성 + 웹 UI 수동 검토용)
    write_packet(run_dir / "packet", prompt, images)

    if args.provider == "packet":
        print(f"packet written: {run_dir / 'packet'}")
        return 0

    names = [n for n, (ok, _) in PROVIDERS.items() if ok()] if args.provider == "auto" else [args.provider]
    names = [n for n in names if PROVIDERS[n][0]()]
    if not names:
        (run_dir / "SKIPPED.md").write_text(
            "# 외부 LLM 교차 검토 건너뜀\n\n"
            "OPENAI_API_KEY / GEMINI_API_KEY 가 설정되지 않아 외부 모델을 호출하지 않았습니다.\n"
            "결과를 임의로 만들지 않았습니다. `packet/` 폴더의 PROMPT.md 와 이미지를 웹 UI에 붙여 넣어\n"
            "수동으로 검토하거나, 키를 설정한 뒤 같은 명령을 다시 실행하세요.\n",
            encoding="utf-8",
        )
        print("SKIPPED: no external LLM API key. packet written to", run_dir / "packet")
        return 3

    status = 0
    for name in names:
        try:
            model, raw = PROVIDERS[name][1](prompt, images)
            (run_dir / f"{name}.raw.json").write_text(raw, encoding="utf-8")
            result = parse_json(raw)
            (run_dir / f"{name}.md").write_text(to_markdown(result, name, model, label), encoding="utf-8")
            print(f"[{name}] score={result.get('overall_score')} verdict={result.get('verdict')} "
                  f"findings={len(result.get('findings', []))}")
            if result.get("verdict") != "pass":
                status = max(status, 1)
        except Exception as e:  # noqa: BLE001 — 공급자 오류는 기록하고 계속
            (run_dir / f"{name}.error.txt").write_text(str(e), encoding="utf-8")
            print(f"[{name}] ERROR: {e}")
            status = 2
    return status


if __name__ == "__main__":
    sys.exit(main())
