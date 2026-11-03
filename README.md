# 처음 배우는 AI 리터러시 — 질문하기부터 에이전트에게 일 맡기기까지

AI 지식이 전혀 없는 **비전공 성인·중장년층**이 학습을 마치면 **에이전틱 AI를 골라 쓰고, 일을 맡기고, 권한을 관리하고, 결과를 검수**할 수 있도록 만든 A4 문제집형 교안입니다.

- 완성본 PDF: [`dist/ai-literacy-workbook.pdf`](dist/ai-literacy-workbook.pdf) (A4, 121쪽)
- 형식: 고등학교 수학 문제집 — 단원 도입 → 개념 익히기 → 예제·유제 → 따라 해 보기 → 확인 문제 → 단원 마무리 → 정답 및 해설
- 디자인: 시안 3종 비교 후 **A안 "정석 네이비"** 채택 → [`design/DESIGN_SYSTEM.md`](design/DESIGN_SYSTEM.md)

## 구성 (4부 12단원 + 부록)

| 부 | 단원 | 핵심 |
|---|---|---|
| 1부 AI와 친해지기 | 01 AI, 이미 우리 곁에 · 02 생성형 AI는 어떻게 말을 만들까 | 규칙형 vs 학습형, 다음 말 예측, 환각·지식 시점·맥락 창 |
| 2부 AI와 대화하기 | 03 첫 대화 시작하기 · 04 프롬프트 기본기 · 05 생활과 일에 AI 쓰기 | 화면 익히기, 4요소(역할·과제·맥락·형식), 고쳐 묻기, 사진 첨부 안전 |
| 3부 믿을 수 있게 쓰기 | 06 AI의 답 확인하기 · 07 안전하고 바르게 쓰기 | 위험도 신호등, 3단계 확인법, 가명 처리, 딥보이스 대처, AI 기본법·저작권 |
| 4부 AI에게 일 맡기기 | 08 챗봇에서 에이전트로 · 09 심부름 6문 · 10 도구 연결과 권한 관리 · 11 작업 루틴 · 12 종합 프로젝트 | 에이전트 루프, 위임 판단표, 위임 지시문, 최소 권한, 승인 화면, 프롬프트 인젝션, 예약 실행, 평가 기준표 |
| 부록 | 템플릿 카드 · 안전 수칙과 연락처 · 서비스 현황(2026.11) · 용어 사전 · 정답 및 해설 | |

## 진행 과정 (자료조사 → 기획 → 제작 → 검증 반복)

전체 기록: [`docs/PROCESS_LOG.md`](docs/PROCESS_LOG.md)

| 단계 | 산출물 |
|---|---|
| 1. 자료조사 | [`docs/research/`](docs/research/) — OECD·EC AI 리터러시 프레임워크(2026), UNESCO(2024), Long & Magerko(2020), 국내 통계, AI 기본법, 개인정보·딥보이스, 에이전트 개념 · [출처 목록](docs/research/SOURCES.md) |
| 2. 기획 | [`docs/plan/curriculum.md`](docs/plan/curriculum.md), 단원별 상세 내용정리 [`docs/plan/units/`](docs/plan/units/), 1차 교차 검토 반영표 [`revision_round1.md`](docs/plan/revision_round1.md) |
| 3. 디자인 | [`design/candidates/`](design/candidates/) 시안 A·B·C, [`design/evaluation.md`](design/evaluation.md) 평가·선정, 디자인 시스템 |
| 4. 제작 | [`textbook/src/*.yaml`](textbook/src/) 원고 → 템플릿·컴포넌트 → HTML → PDF |
| 5. 검증 | 자동 검증 [`reports/verify/`](reports/verify/), 교차 검토 [`reports/crossreview/`](reports/crossreview/) |

## 하네스 (빌드·검증·교차 검토)

```bash
# 전체 검증: 원고 검사 → 빌드 → PDF·레이아웃 검사 → 보고서
bash harness/verify.sh          # 결과: reports/verify/LATEST.md, dist/ai-literacy-workbook.pdf
bash harness/verify.sh --png    # 페이지 PNG까지 (dist/png/)
```

| 도구 | 하는 일 |
|---|---|
| `harness/build.py` | YAML 원고 → A4 고정 페이지 HTML (Jinja2 템플릿 `textbook/templates/`) |
| `harness/render.mjs` | Playwright(Chromium)로 PDF·PNG 출력 + 레이아웃 검사: 본문 넘침, 최소 글자 10.5pt, 페이지당 줄글 800자, 긴 문장, 개념 페이지 시각 자료, 그림 칸 넘침, 채움 비율 |
| `harness/check.py` | 원고 검사: 정답 누락, 단원 구조, 단원별 주의 상자, 문제 번호, 약어 풀이, 제품명, 표 칸 수, 선택지 수, YAML 쉼표 잘림 |
| `harness/crossreview/review.py` | **외부 LLM 교차 검토** (GPT·Gemini). 같은 채점 기준(`rubrics/plan·design·pages`)으로 검토받아 `reports/crossreview/<label>/`에 저장 |

### 외부 LLM(GPT·Gemini) 교차 검토 켜기

이 저장소를 만든 클라우드 세션에서는 `api.openai.com`이 네트워크 정책으로 막혀 있었고 API 키도 없었습니다. 그래서 교차 검토는 **맥락이 분리된 독립 리뷰어(별도 Claude 에이전트)**로 대신했고, 외부 LLM의 결과는 만들어 내지 않았습니다(각 폴더의 `SKIPPED.md`).

외부 검토를 실행하려면:

1. 환경 설정에 API 키를 넣습니다: `OPENAI_API_KEY` 또는 `GEMINI_API_KEY` (클라우드 환경이면 Network access 에 `api.openai.com` 허용도 필요)
2. 실행합니다.
   ```bash
   python harness/crossreview/review.py --rubric pages --pdf dist/ai-literacy-workbook.pdf --pages 1-46 --label gpt-pages-1
   # 모델 바꾸기: CROSSREVIEW_OPENAI_MODEL / CROSSREVIEW_GEMINI_MODEL
   ```
3. 키 없이도 **수동 교차 검토**를 할 수 있습니다. 매 실행마다 `reports/crossreview/<label>/packet/`에 `PROMPT.md`와 페이지 이미지가 생기므로, ChatGPT·Gemini 웹 화면에 그대로 붙여 넣으면 됩니다.

## 원고 고치기

- 원고는 `textbook/src/NN_unitNN.yaml` 한 곳에만 있습니다. 한 페이지 = `pages:` 아래 한 항목.
- 쓸 수 있는 블록(`p`, `concept`, `figure`, `table`, `example`, `exercises` …)과 그림 종류는 [`design/DESIGN_SYSTEM.md`](design/DESIGN_SYSTEM.md) 5장에 정리되어 있습니다.
- 쉼표·물음표가 든 문장은 `"따옴표"`로 감싸세요. (`check.py`의 `yaml-split`·`table-cols`·`choices` 검사가 잡아 줍니다)
- 확인 문제의 `answer`·`explain`은 자동으로 부록 "정답 및 해설"에 모입니다.

## 라이선스와 글꼴

- 글꼴: Pretendard, Noto Serif KR, Black Han Sans, Nanum Pen Script — 모두 SIL Open Font License 1.1 (`textbook/assets/fonts/`, 한글 범위로 서브셋)
- 화면 그림은 특정 회사의 화면이 아니라 여러 서비스의 공통 모양을 정리한 모식도입니다.
