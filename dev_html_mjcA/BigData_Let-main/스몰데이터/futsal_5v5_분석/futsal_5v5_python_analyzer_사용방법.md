# 풋살 5대5 CSV × Python 분석 실습

## 다운로드 파일

- `futsal_5v5_python_analyzer.html`: 메인 브라우저 분석 웹앱. CSS/JavaScript/6개 Python 분석 셀/샘플 데이터를 단일 HTML에 포함
- `futsal_5v5_ai_match_positions_sample.csv`: 이전 자동 5대5 풋살 게임에서 생성된 2,010행 샘플
- `futsal_5v5_colab_analysis.ipynb`: Google Colab에서 실행 가능한 Python 노트북
- `futsal_5v5_python_analysis.py`: 로컬 Python 분석 및 PNG 그래프 생성 코드

## 방법 A: 브라우저에서 실제 Python 분석

1. `futsal_5v5_python_analyzer.html`을 Chrome/Edge에서 열기
2. 자동 풋살 게임에서 `CSV 다운로드` → 이 웹앱에서 `CSV 업로드` 클릭
3. 별도 CSV가 없는 경우 웹앱의 `게임 예제 데이터 불러오기`로 즉시 연습
4. `▶ Python 전체 실행` 클릭 → 6개 Python 셀(pandas, numpy) 실제 실행
5. 히트맵, 선수별 추정 이동거리, 팀 비교, 시간대별 그래프 확인
6. 선수/팀 선택 및 시간 슬라이더 조절 → Python 분석 내용 다시 계산
7. `분석표 CSV 저장` 또는 `인포그래픽 HTML 저장`

**중요:** 브라우저는 Python을 설치하지 않아도 되지만 Pyodide v314.0.7과 pandas/numpy를 jsDelivr에서 **처음 불러올 때 인터넷 연결이 필요**합니다. 외부 인터넷이 차단된 경우 실제 Python 실행은 불가하며, 초기 HTML 인터페이스의 JavaScript 미리보기는 오프라인으로 작동합니다. 첫 실행에 라이브러리 다운로드가 필요합니다.

## 방법 B: Google Colab 실습

1. https://colab.research.google.com/ 열기
2. `파일 → 노트 업로드` → `futsal_5v5_colab_analysis.ipynb` 선택
3. `런타임 → 모두 실행`
4. 업로드 창에서 자동 풋살 게임 CSV 선택 (혹은 함께 제공한 샘플 CSV)
5. 위치 데이터, 결측치/중복 정리, 10명 이동거리, 공간 히트맵, 팀 분석 그래프 확인
6. 마지막 셀에서 분석 CSV와 PNG가 포함된 ZIP 다운로드

## 데이터 정의

필수 열: `game_time_sec, team, player_id, x_m, y_m`
선택 열: `role, ball_owner, ball_x_m, ball_y_m, sample_id, number, source`
팀: A(BLUE) / B(ORANGE), 선수: A1~A5 / B1~B5, 좌표: 40m × 20m 경기장

### 주의할 통계 해석

- 이동거리는 저장된 두 좌표 사이의 직선 거리를 합산한 *추정값*입니다. 실제 경로보다 작을 수 있습니다.
- `ball_owner=1`의 기록 수는 실제 점유 시간 또는 득점·패스 횟수를 의미하지 않습니다.
- 히트맵은 관측된 위치의 공간적 밀도입니다. 동일 좌표수는 동일한 이동거리를 뜻하지 않습니다.
- 예제 CSV는 **가상 AI 경기 데이터**입니다. 실제 선수 생체 데이터는 없습니다.

## 검증 범위

Python 분석 6개 셀과 `.py` 그래프 생성은 로컬 CPython 환경에서 실행 테스트했습니다. 브라우저에서 CSV 파일 업로드, 필터, 미리보기, 히트맵과 파일 다운로드, 모바일 레이아웃을 확인했습니다. Pyodide CDN에 접속하는 외부 네트워크가 테스트 환경에서 차단되어 브라우저 내부 Python 엔진의 다운로드 완료 및 실행까지는 검증하지 못했습니다. CDN 버전 및 pandas/numpy 패키지 존재는 Pyodide 공식 문서로 확인했습니다.
