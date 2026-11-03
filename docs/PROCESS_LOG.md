# 진행 기록 (PROCESS LOG)

> 사용자 요구 순서: **자료조사 → 기획 → 제작 → 검증 반복**, 중간중간 하네스 구축과 외부 LLM 교차 검토

| 단계 | 일시 | 산출물 | 메모 |
|---|---|---|---|
| 0. 환경 점검 | 2026-11-03 | — | 빈 저장소. 외부 LLM: `api.openai.com` 네트워크 정책으로 막힘, Gemini 엔드포인트는 열려 있으나 키 없음 → 교차 검토 하네스는 키가 생기면 바로 쓰게 만들고, 이번 세션은 **독립 리뷰어(분리된 맥락의 별도 에이전트)**로 대체. 외부 검토 결과는 만들어 내지 않음 |
| 1. 자료조사 | 2026-11-03 | `docs/research/01~04`, `SOURCES.md` | OECD·EC AILit(2026.6 최종), UNESCO 2024, Long&Magerko 2020, 국내 통계, AI 기본법, 개인정보위 안내서, 딥보이스, 에이전트 개념(Anthropic·OpenAI) |
| 2. 기획 | 2026-11-03 | `docs/plan/curriculum.md`, `docs/plan/units/part1~4` | 4부 12단원, 문제집형 페이지 유형 6종, 밀도 규칙 |
| ✔ 하네스 ① | 2026-11-03 | `harness/crossreview/review.py` + rubrics(plan/design/pages) | OpenAI/Gemini 호출, 키 없으면 SKIPPED + 수동 검토 packet |
| ✔ 교차 검토 1차 (기획) | 2026-11-03 | `reports/crossreview/round1-plan/` | 독립 리뷰어 71점 revise (C2·M11·m5) → 18건 중 17건 수용, 1건 부분 수용 → `docs/plan/revision_round1.md`. 사실 확인 검색 4건 추가 |
| 3. 디자인 시안 | 2026-11-03 | `design/candidates/` (A·B·C 각 4쪽 PDF·PNG) | 같은 HTML + CSS만 다른 3종 → 공정 비교. 하네스 빌드·렌더 검사 통과(오류 0) |
| ✔ 교차 검토 2차 (디자인) | 2026-11-03 | `reports/crossreview/round2-design/` | 독립 리뷰어 A 26 · B 20 · C 25 / 제작자 A 28 · B 24 · C 23 → **A 채택**. 지적 5건 반영(곁단 48mm, 메모 11.5pt, 별·막대 대비, 손글씨 제거, 컴포넌트 고정) → `design/DESIGN_SYSTEM.md` |
| ✔ 하네스 ② | 2026-11-03 | `harness/build.py`, `render.mjs`, `check.py`, `report.py`, `verify.sh` | 원고 검사(정답·구조·주의 상자·약어·제품명) + 레이아웃 검사(넘침·최소 글자·줄글 분량·문장 길이·시각 자료·채움) |
