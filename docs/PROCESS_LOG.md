# 진행 기록 (PROCESS LOG)

> 사용자 요구 순서: **자료조사 → 기획 → 제작 → 검증 반복**, 중간중간 하네스 구축과 외부 LLM 교차 검토

| 단계 | 일시 | 산출물 | 메모 |
|---|---|---|---|
| 0. 환경 점검 | 2026-11-03 | — | 빈 저장소. 외부 LLM: `api.openai.com` 네트워크 정책으로 막힘, Gemini 엔드포인트는 열려 있으나 키 없음 → 교차 검토 하네스는 키가 생기면 바로 쓰게 만들고, 이번 세션은 **독립 리뷰어(분리된 맥락의 별도 에이전트)**로 대체. 외부 검토 결과는 만들어 내지 않음 |
| 1. 자료조사 | 2026-11-03 | `docs/research/01~04`, `SOURCES.md` | OECD·EC AILit(2026.6 최종), UNESCO 2024, Long&Magerko 2020, 국내 통계, AI 기본법, 개인정보위 안내서, 딥보이스, 에이전트 개념(Anthropic·OpenAI) |
| 2. 기획 | 2026-11-03 | `docs/plan/curriculum.md`, `docs/plan/units/part1~4` | 4부 12단원, 문제집형 페이지 유형 6종, 밀도 규칙 |
| ✔ 하네스 ① | 2026-11-03 | `harness/crossreview/review.py` + rubrics(plan/design/pages) | OpenAI/Gemini 호출, 키 없으면 SKIPPED + 수동 검토 packet |
| ✔ 교차 검토 1차 (기획) | 2026-11-03 | `reports/crossreview/round1-plan/` | 독립 리뷰어 71점 revise (C2·M11·m5) → 18건 중 17건 수용, 1건 부분 수용 → `docs/plan/revision_round1.md`. 사실 확인 검색 4건 추가 |
