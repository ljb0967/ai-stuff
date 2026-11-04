# 작업 인수인계 (HANDOFF)

> 새 세션은 **이 파일부터** 읽고 이어서 작업한다. 단계가 끝날 때마다 이 파일을 갱신한다.
> 마지막 갱신: 2026-11-03 (4차 반영 완료) · 브랜치 `claude/ai-literacy-curriculum-tpah6j`

## 0. 한 줄 요약

AI 지식이 없는 중장년·비전공자용 **A4 문제집형 AI 리터러시 교안**(4부 12단원 + 부록, **122쪽**)이 완성되었다. 3차 교차 검토 39건 반영 → 4차 반영 확인 검토(33/39 확인 + 나머지 직접 확인, 새 문제 3건 수정)까지 끝났고 자동 검증 **PASS**(오류 0·경고 0). **남은 것: GitHub 푸시(권한 문제), 외부 LLM(GPT·Gemini) 검토.**

## 1. 사용자 요구사항 (원문 요지)

1. 새 저장소에 **AI 문해력 향상 교안** 작성 프로젝트. 대상: AI 지식이 없는 비전공자·중장년층. 목표: 학습 후 **에이전틱 AI를 자유자재로** 사용.
2. 기초부터 차근차근. **고등학교 수학 문제집처럼** 디자인, **A4** 판형.
3. 한 페이지에 내용을 너무 많이 넣지 말 것. 본문 줄글 + **참조 이미지와 도표 자료** 첨부.
4. 디자인 일관성: **처음에 시안을 여러 개 뽑아 가장 적합한 것을 골라** 그 디자인으로 유지 → 완료(A안).
5. 교안에 들어갈 **AI 리터러시 내용정리를 자세히** 한 뒤 개발 → 완료(`docs/plan/units/`).
6. 프로세스: **자료조사 → 기획 → 제작 → 검증 반복**. 중간중간 **하네스 구축**, **외부 LLM(GPT 등) 교차 검토**.
7. (추가 요청) 새 세션에서 바로 이어 갈 수 있게 **md 파일에 정리하며 진행** → 이 파일 + `CLAUDE.md`.

## 2. 진행 상황

| 단계 | 상태 | 산출물 |
|---|---|---|
| 1. 자료조사 | ✅ 완료 | `docs/research/01~04`, `SOURCES.md` |
| 2. 기획 | ✅ 완료 | `docs/plan/curriculum.md`, `docs/plan/units/part1~4`, 1차 검토 반영 `docs/plan/revision_round1.md` |
| 3. 디자인 시안·선정 | ✅ 완료 | `design/candidates/`(A·B·C), `design/evaluation.md`, **`design/DESIGN_SYSTEM.md`(고정 규칙)** |
| 4. 하네스 | ✅ 완료 | `harness/build.py`, `render.mjs`, `check.py`, `report.py`, `verify.sh`, `crossreview/review.py` |
| 5. 제작 | ✅ 초안 완료 | `textbook/src/*.yaml` → `dist/ai-literacy-workbook.pdf` (121쪽) |
| 6. 검증 반복 | ✅ 1차 사이클 완료 | 자동 검증 PASS (`reports/verify/LATEST.md`). 교차 검토 4회 반영 ↓ |

### 교차 검토 이력

| 회차 | 대상 | 검토자 | 결과 | 반영 |
|---|---|---|---|---|
| 1차 | 기획 문서 | 독립 리뷰어(별도 Claude 에이전트) | 71점 revise (critical 2, major 11, minor 5) | ✅ `docs/plan/revision_round1.md` (17건 수용, 1건 부분 수용) |
| 2차 | 디자인 시안 3종 | 독립 리뷰어 | A 26 · C 25 · B 20 → **A 채택** | ✅ `design/evaluation.md` (지적 5건 반영) |
| 3차 | 완성 페이지 p.1–46 / 47–84 / 85–121 | 독립 리뷰어 3명(구간별) | 72 · 74 · 71점, 모두 revise (critical 2, major 20) | ✅ 39건 반영 → `docs/plan/revision_round3.md` |
| 4차 | 3차 반영 확인(바뀐 47쪽) | 독립 리뷰어 | 80점, 33/39 확인 · 미반영 1 · 새 문제 minor 3 | ✅ `docs/plan/revision_round4.md` |
| 5차 | 전체 122쪽 | **외부 LLM(GPT/Gemini)** | ⏳ 사용자 실행 대기 (키 없음 → 수동 안내 `round5-external/MANUAL.md`) | ⬜ |

> 외부 LLM(GPT·Gemini) 검토는 아직 **한 번도 실행되지 않았다**(키·네트워크 없음, 4장 참고). 결과를 지어내지 않았고, 각 회차 폴더에 `SKIPPED.md`와 수동 검토용 `packet/`이 있다.

## 3. 다음에 할 일 (우선순위 순)

1. **GitHub 푸시** (4장 참고). 지금까지의 커밋은 로컬에만 있다. 권한이 고쳐지면 `git push -u origin claude/ai-literacy-curriculum-tpah6j`.
   - 이 세션에서 끝내 푸시하지 못한 경우: 이 세션이 남긴 `ai-stuff.bundle`(git bundle)을 내려받아 내 컴퓨터에서 `git clone ai-stuff.bundle ai-stuff && cd ai-stuff && git push origin claude/ai-literacy-curriculum-tpah6j`.
2. **외부 LLM 교차 검토(5차)** — 자료 준비 완료(2026-11-04): 수동 실행 안내 `reports/crossreview/round5-external/MANUAL.md`(PDF 첨부 + 붙여 넣을 글), API용 묶음 `reports/crossreview/round5-external-a|b|c/packet/`. 키가 생기면 GPT·Gemini로 전체를 다시 검토한다. 결과는 `docs/plan/revision_round5.md`에 반영표로 남긴다.
   `python harness/crossreview/review.py --rubric pages --pdf dist/ai-literacy-workbook.pdf --pages 1-46 --label gpt-r5a` (47-84, 85-122도 같은 방식)
   키 없이도 각 `reports/crossreview/*/packet/PROMPT.md`와 이미지를 ChatGPT·Gemini 웹에 붙여 수동 검토 가능.
3. 원고를 고칠 때마다 `bash harness/verify.sh --png` → **RESULT: PASS** 확인.
4. (선택) 강사용 지도안, 실습용 가상 자료(공문·설문 예시 파일), 흑백 인쇄 점검, 서비스 현황표(부록 C) 정기 갱신.

## 4. 알려진 문제와 해결 방법

| 문제 | 상태 | 해결 |
|---|---|---|
| **GitHub 푸시 403** — "Claude doesn't have GitHub access to ljb0967/ai-stuff" | ❌ 미해결(2026-11-04 재확인: GitHub MCP는 ljb0967로 인증되고 저장소는 빈 상태, git 푸시만 Claude GitHub App 미설치로 거부). **로컬 커밋만 있고 원격에 없음** | 사용자가 https://claude.ai/connect-github 에서 GitHub 재연결 / Claude GitHub App을 저장소에 설치. 그 뒤 `git push -u origin claude/ai-literacy-curriculum-tpah6j` |
| 외부 LLM 교차 검토 불가 | ❌ 미해결 | `api.openai.com`은 네트워크 정책에서 막힘 → 환경 설정 Network access에 허용 추가. Gemini 엔드포인트는 열려 있음. 환경 변수 `OPENAI_API_KEY` 또는 `GEMINI_API_KEY` 설정(새 세션부터 적용). 키 없이도 `packet/PROMPT.md`를 웹 UI에 붙여 수동 검토 가능 |
| 원문 PDF 일부 미열람 | ⚠ | 세션 네트워크 제한으로 OECD·UNESCO 원문은 웹 검색 요약으로 대신함(`docs/research/*`에 ⚠ 표시) |

## 5. 다시 시작하는 법

```bash
cd ai-stuff
git checkout claude/ai-literacy-curriculum-tpah6j
pip install jinja2 pyyaml pypdfium2 pillow fonttools brotli   # 대부분 기본 설치됨
bash harness/verify.sh --png        # 원고 검사 → 빌드 → PDF·PNG → 레이아웃 검사
# 결과: dist/ai-literacy-workbook.pdf, dist/png/page-###.png, reports/verify/LATEST.md
```

- 브라우저: 세션에 깔린 Playwright(Node) 사용. `render.mjs`는 `createRequire`로 전역 playwright를 불러온다(별도 설치 금지).
- 페이지 몇 장만 뽑기: `node harness/render.mjs --html dist/book.html --png dist/png --pages 66-75 --report /tmp/l.json`

## 6. 파일 지도

```
README.md                      프로젝트 소개·사용법
HANDOFF.md                     ← 이 파일 (진행 상황·다음 할 일)
CLAUDE.md                      새 세션 Claude가 자동으로 읽는 작업 규칙
docs/research/                 자료조사 (프레임워크, 학습자, 에이전트, 국내 제도) + SOURCES.md
docs/plan/curriculum.md        교안 기획서 (단원 구성·페이지 규칙)
docs/plan/units/part1~4_*.md   단원별 상세 내용정리 (교사용 수준)
docs/plan/revision_round1.md   1차 교차 검토 반영표 (기획 문서보다 우선)
docs/PROCESS_LOG.md            단계별 진행 기록
design/DESIGN_SYSTEM.md        고정 디자인 규칙 (색·글꼴·컴포넌트 목록)
design/evaluation.md           시안 평가·선정 근거
design/candidates/             시안 A·B·C (PDF·PNG·CSS)
textbook/src/NN_*.yaml         ★ 원고 (00 앞부분, 01~12 단원, 99 부록)
textbook/templates/            book.html.j2(페이지 틀), blocks.html.j2(컴포넌트)
textbook/assets/css/           base.css(구조), theme-a.css(채택 디자인)
textbook/assets/fonts/         OFL 글꼴 (한글 서브셋)
harness/                       빌드·검사·교차 검토 도구
reports/verify/                자동 검증 보고서 (LATEST.md)
reports/crossreview/           교차 검토 결과·수동 검토 packet
dist/ai-literacy-workbook.pdf  완성본
```

## 7. 단원별 쪽수 (현재 빌드 기준)

| 구간 | 쪽 |
|---|---|
| 앞부분(표지·머리말·구성·등장인물·차례) | 1–5 |
| 1부 (간지, 01, 02) | 6–21 |
| 2부 (간지, 03, 04, 05) | 22–46 |
| 3부 (간지, 06, 07) | 47–64 |
| 4부 (간지, 08, 09, 10, 11, 12) | 65–110 |
| 부록 A~E (정답 및 해설 6쪽) | 111–122 |

## 8. 결정 사항 (바꾸려면 사용자와 상의)

- 디자인 **A안 "정석 네이비"** 고정. 본문 13pt, 캡션 최소 10.5pt, 곁단 48mm.
- 본문에 **제품명 쓰지 않음**(사건·통계 출처, 부록 C 제외). 화면 그림은 일반화된 모식도.
- 위임 지시문 이름은 **"심부름 6문"**(목표·배경·자료·완료 기준·하지 말 것·확인 시점).
- 위임 판단표 축: **아끼는 시간 × 되돌릴 수 있는가**.
- 등장인물 4명: 김정숙(62, 은퇴 교사·독서 모임 총무), 박영호(55, 빵집 사장), 이수진(45, 구청 행정직), 최민호(29, 취업 준비생).
