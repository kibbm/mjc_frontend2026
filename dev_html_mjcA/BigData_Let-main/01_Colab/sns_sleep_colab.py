# -*- coding: utf-8 -*-
# %% [markdown]
# # SNS × 수면: 우리 학교 학년별 빅데이터·스몰데이터 실습
# **고등학생 특강 | 수집 → 저장 → 전처리 → 분석 → 시각화·예측**
# 
# 이 데이터는 **가상 학교 학생 900명의 익명 합성 데이터**입니다. 실제 학교/학생을 조사한 결과가 아닙니다.
# 실습에서는 Colab 내부에 데모 웹서버를 열어 HTTP 요청으로 HTML 표를 크롤링하므로
# 외부 사이트 접속이 차단되어도 전체 과정을 실행할 수 있습니다.
# 
# 분석 결과의 상관관계는 인과관계가 아닙니다. 미래예측은 **가상의 SNS 사용시간 시나리오**이며
# 실제 학생의 수면이나 건강을 진단하는 정보가 아닙니다.

# %% [markdown]
# ## 0. 환경 설정
# Google Colab 기본 런타임에 포함된 `pandas`, `numpy`, `requests`, `beautifulsoup4`,
# `matplotlib`, `scikit-learn`을 사용합니다. **파일 업로드 없이 [런타임 → 모두 실행]**할 수 있습니다.

# %%
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from html import escape
from io import StringIO
from zipfile import ZipFile, ZIP_DEFLATED
import sys, re

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt

OUTPUT_DIR = Path.cwd() / "SNS_SLEEP_실습결과"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SEED = 20261023
# 교사가 공개한 같은 형식의 HTML 페이지 URL을 넣으면 실제 원격 웹페이지 크롤링을 시도합니다.
# 예) PUBLIC_CLASS_PAGE_URL = 'https://username.github.io/repo/sns_sleep_survey_source.html'
# 기본값('')은 모든 Colab에서 동작하는 로컬 HTTP 웹사이트를 사용합니다.
PUBLIC_CLASS_PAGE_URL = ""

print("실습 파일 저장 위치:", OUTPUT_DIR)

# %% [markdown]
# ## 1. 수집 준비: 익명 설문 웹페이지 생성
# 1·2·3학년 각각 300명, 합계 900명의 **가상 익명 데이터**를 생성합니다.
# 수집·전처리 실습을 위해 중복 행, 누락값, 비정상 숫자 12행을 일부러 추가합니다.
# `record_no`는 실습용 행 번호로, 학번·이름이 아닙니다.

# %%
def make_demo_raw(seed=SEED):
    rng = np.random.default_rng(seed)
    rows = []
    idx = 1
    for grade in [1, 2, 3]:
        for _ in range(300):
            sns = int(np.clip(round(rng.normal(147 + 29 * grade, 65)), 10, 520))
            late_probability = 1 / (1 + np.exp(-(-0.35 + (sns - 165) / 115 + 0.13 * grade)))
            late = "Y" if rng.random() < late_probability else "N"
            # 통계 예제용 데이터 생성식일 뿐, 실제 인과관계를 나타내지 않습니다.
            sleep = int(np.clip(round(563 - 14 * grade - 0.25 * sns - (late == "Y") * 20 + rng.normal(0, 51)), 205, 630))
            rows.append({"record_no": f"R{idx:04d}", "grade": grade,
                         "sns_minutes": sns, "sleep_minutes": sleep,
                         "late_night_sns": late})
            idx += 1
    raw = pd.DataFrame(rows, columns=["record_no", "grade", "sns_minutes", "sleep_minutes", "late_night_sns"])
    anomalies = raw.iloc[[4, 77, 302]].copy() # 일부러 넣은 중복 3건
    faulty = pd.DataFrame([
        {"record_no":"E0001","grade":1,"sns_minutes":175,"sleep_minutes":"","late_night_sns":"N"},
        {"record_no":"E0002","grade":2,"sns_minutes":110,"sleep_minutes":"","late_night_sns":"Y"},
        {"record_no":"E0003","grade":3,"sns_minutes":190,"sleep_minutes":"","late_night_sns":"Y"},
        {"record_no":"E0004","grade":1,"sns_minutes":-30,"sleep_minutes":470,"late_night_sns":"N"},
        {"record_no":"E0005","grade":2,"sns_minutes":980,"sleep_minutes":400,"late_night_sns":"Y"},
        {"record_no":"E0006","grade":3,"sns_minutes":700,"sleep_minutes":395,"late_night_sns":"Y"},
        {"record_no":"E0007","grade":4,"sns_minutes":200,"sleep_minutes":435,"late_night_sns":"Y"},
        {"record_no":"E0008","grade":1,"sns_minutes":230,"sleep_minutes":440,"late_night_sns":"?"},
        {"record_no":"E0009","grade":"?","sns_minutes":170,"sleep_minutes":450,"late_night_sns":"N"},
    ])
    return pd.concat([raw, anomalies, faulty], ignore_index=True).astype(str)


def make_html_table(raw):
    headers = ["record_no", "grade", "sns_minutes", "sleep_minutes", "late_night_sns"]
    thead = "".join(f"<th scope='col'>{escape(k)}</th>" for k in headers)
    trs = []
    for row in raw[headers].itertuples(index=False, name=None):
        tds = "".join(f"<td>{escape(str(v))}</td>" for v in row)
        trs.append(f"<tr>{tds}</tr>")
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
      "<title>가상 학교의 익명 SNS·수면 설문 (교육용)</title>"
      "<style>body{font:16px system-ui,sans-serif;max-width:960px;margin:40px auto;color:#243047}"
      "h1{color:#4b398d}p{line-height:1.6}table{border-collapse:collapse;width:100%}"
      "td,th{border:1px solid #d9dbe8;padding:8px;text-align:left}"
      "th{position:sticky;top:0;background:#ede9fe}tr:nth-child(even){background:#f8fafc}</style>"
      "</head><body><h1>가상 학교 SNS × 수면 설문 결과</h1>"
      "<p><strong>안내:</strong> 실제 학교 자료가 아닌, 수업 실습용 익명 합성 데이터입니다. "
      "학생 이름·학번·연락처는 포함하지 않습니다. 데이터에는 중복·오류가 의도적으로 삽입되어 있습니다.</p>"
      "<table id='survey-table'><thead><tr>" + thead + "</tr></thead><tbody>" +
      "".join(trs) + "</tbody></table></body></html>")

raw_generated = make_demo_raw()
source_html_path = OUTPUT_DIR / "sns_sleep_survey_source.html"
source_html_path.write_text(make_html_table(raw_generated), encoding="utf-8")
print("원자료 웹페이지 생성:", source_html_path.name, f"({len(raw_generated):,}행)")

# %% [markdown]
# ## 2. 수집: requests + BeautifulSoup으로 실제 HTTP/HTML 크롤링
# 먼저 로컬 HTTP 서버를 열고 그 주소로 `requests.get()`을 보냅니다.
# 받아온 HTML의 `<table id="survey-table">`을 `BeautifulSoup`으로 읽습니다.
# URL을 직접 입력하는 선택 옵션도 있지만 **기본 실습은 인터넷 없이 실행**됩니다.
# 
# *외부 실존 학교 홈페이지·학생 개인정보 페이지를 무단 크롤링하지 않습니다.*

# %%
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def crawl_table(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.select_one("table#survey-table")
    if table is None:
        raise ValueError("웹페이지에서 id='survey-table'인 표를 찾을 수 없습니다.")
    columns = [x.get_text(strip=True) for x in table.select("thead th")]
    records = [[td.get_text(strip=True) for td in tr.select("td")]
               for tr in table.select("tbody tr")]
    records = [r for r in records if len(r) == len(columns)]
    return pd.DataFrame(records, columns=columns)


def http_crawl_demo(directory, file_name, remote_url=""):
    if remote_url.strip():
        try:
            print("원격 공개 페이지 HTTP 크롤링 시도:", remote_url)
            response = requests.get(remote_url, timeout=12, headers={"User-Agent":"SchoolDataEducationDemo/1.0"})
            response.raise_for_status()
            return crawl_table(response.text), remote_url
        except Exception as ex:
            print("원격 접속 실패, Colab 내부 웹서버 방식으로 계속합니다:", type(ex).__name__)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(directory)))
    th = Thread(target=server.serve_forever, daemon=True)
    th.start()
    url = f"http://127.0.0.1:{server.server_address[1]}/{file_name}"
    try:
        session = requests.Session()
        session.trust_env = False  # Colab의 외부 HTTP 프록시 설정과 무관하게 localhost 접속
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return crawl_table(response.text), url
    finally:
        server.shutdown()
        server.server_close()
        th.join(timeout=2)

raw_collected, collected_url = http_crawl_demo(OUTPUT_DIR, source_html_path.name, PUBLIC_CLASS_PAGE_URL)
print("크롤링 주소:", collected_url)
print("HTML 표에서 수집한 행:", len(raw_collected))
print(raw_collected.head(5).to_string(index=False))

# %% [markdown]
# ### 선택 실습: 우리 학교의 승인된 익명 CSV 업로드
# 실제로 익명 설문을 진행했고 학교의 정보보호·동의 지침을 준수한 경우에만 아래
# `USE_UPLOADED_CSV`를 `True`로 변경합니다. 업로드 파일은 가급적 학교 명칭도 넣지 않고,
# `grade,sns_minutes,sleep_minutes,late_night_sns` 네 열(권장: `record_no` 포함)을 사용합니다.
# 기본값은 `False`이므로 파일 없이 전 과정이 실행됩니다.

# %%
USE_UPLOADED_CSV = False
if USE_UPLOADED_CSV:
    from google.colab import files
    uploaded = files.upload()
    chosen = next((name for name in uploaded if name.lower().endswith(".csv")), None)
    if chosen is None:
        raise ValueError("CSV 파일을 선택해 주세요.")
    raw_collected = pd.read_csv(StringIO(uploaded[chosen].decode("utf-8-sig")), dtype=str, keep_default_na=False)
    print("승인된 익명 설문 CSV로 교체 완료:", chosen, len(raw_collected), "행")

# %% [markdown]
# ## 3. 저장: 수집 결과를 CSV로 저장
# CSV는 Excel과 Google Sheets에서 열 수 있는 쉼표 구분 텍스트입니다.
# `utf-8-sig`로 저장하면 Windows Excel에서도 한글 호환성이 좋습니다.

# %%
raw_csv_path = OUTPUT_DIR / "sns_sleep_raw.csv"
raw_collected.to_csv(raw_csv_path, index=False, encoding="utf-8-sig")
print("수집 CSV 저장 완료:", raw_csv_path)

# %% [markdown]
# ## 4. 처리: CSV 다시 읽기 → 결측값 / 중복 / 범위 오류 정제
# 데이터를 일부러 다시 CSV에서 읽습니다. 사용 시간·수면 시간은 모두 **분 단위**입니다.
# 수업용 유효범위는 SNS 0–600분, 수면 180–720분, 학년 1–3학년, 야간 SNS Y/N으로 정합니다.
# 이 값은 **데이터 정제 실습 기준**이지 의료·건강 판정 기준은 아닙니다.

# %%
def clean_survey(df):
    frame = df.copy()
    needed = ["grade", "sns_minutes", "sleep_minutes", "late_night_sns"]
    if not set(needed).issubset(frame.columns):
        raise ValueError("필수 CSV 열: " + ", ".join(needed))
    if "record_no" not in frame.columns:
        frame.insert(0, "record_no", [f"U{i:05d}" for i in range(1, len(frame) + 1)])
    total = len(frame)
    frame["record_no"] = frame["record_no"].astype(str).str.strip()
    frame = frame.drop_duplicates(subset="record_no", keep="first").copy()
    duplicates_removed = total - len(frame)
    frame["grade"] = frame["grade"].astype(str).str.replace("학년", "", regex=False).str.strip()
    for name in ["grade", "sns_minutes", "sleep_minutes"]:
        frame[name] = (frame[name].astype(str)
                        .str.replace("분", "", regex=False)
                        .str.replace(",", "", regex=False).str.strip())
        frame[name] = pd.to_numeric(frame[name], errors="coerce")
    frame["late_night_sns"] = frame["late_night_sns"].astype(str).str.upper().str.strip()
    frame["late_night_sns"] = frame["late_night_sns"].replace({"YES":"Y", "NO":"N", "1":"Y", "0":"N"})
    frame = frame.dropna(subset=["grade", "sns_minutes", "sleep_minutes"])
    frame = frame[(frame.grade.isin([1,2,3])) &
                  (frame.sns_minutes.between(0,600)) &
                  (frame.sleep_minutes.between(180,720)) &
                  (frame.late_night_sns.isin(["Y", "N"]))].copy()
    frame["grade"] = frame["grade"].astype(int)
    frame["sns_minutes"] = frame["sns_minutes"].round().astype(int)
    frame["sleep_minutes"] = frame["sleep_minutes"].round().astype(int)
    frame["sns_hours"] = (frame["sns_minutes"] / 60).round(3)
    frame["sleep_hours"] = (frame["sleep_minutes"] / 60).round(3)
    frame["late_flag"] = (frame["late_night_sns"] == "Y").astype(int)
    return frame.reset_index(drop=True), {"raw": total, "duplicates": duplicates_removed,
                                         "invalid_or_missing": total - duplicates_removed - len(frame),
                                         "clean":len(frame)}

loaded_raw = pd.read_csv(raw_csv_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
clean, quality = clean_survey(loaded_raw)
clean_path = OUTPUT_DIR / "sns_sleep_clean.csv"
clean.to_csv(clean_path, index=False, encoding="utf-8-sig")
small = (pd.concat([part.sample(n=min(10, len(part)), random_state=42)
                    for _, part in clean.groupby("grade")], ignore_index=True)
              .sort_values(["grade", "record_no"]).reset_index(drop=True))
small_path = OUTPUT_DIR / "sns_sleep_small30.csv"
small.to_csv(small_path, index=False, encoding="utf-8-sig")
print("데이터 품질:", quality)
print("전체 정제 자료:", clean_path.name, len(clean), "행")
print("스몰데이터:", small_path.name, len(small), "행")

# %% [markdown]
# ## 5. 분석: 학년별 SNS·수면 평균, 상관계수, 소표본 비교
# SNS 시간이 길수록 수면도 짧은 경향이 보이는지 **상관관계**를 계산합니다.
# 작은 표본의 결과가 전체 표본과 왜 다를 수 있는지도 확인합니다.

# %%
def summarize(df):
    return (df.groupby("grade").agg(
        students=("record_no", "count"),
        mean_sns_minutes=("sns_minutes", "mean"),
        mean_sleep_minutes=("sleep_minutes", "mean"),
        share_sleep_under7=("sleep_minutes", lambda s: (s < 420).mean() * 100),
        late_sns_share=("late_flag", lambda s: s.mean() * 100),
    ).round(2).reset_index())

by_grade = summarize(clean)
by_grade.to_csv(OUTPUT_DIR / "sns_sleep_grade_summary.csv", index=False, encoding="utf-8-sig")
cor_full = float(clean["sns_minutes"].corr(clean["sleep_minutes"]))
cor_small = float(small["sns_minutes"].corr(small["sleep_minutes"]))
print("학년별 전체 데이터 요약")
print(by_grade.to_string(index=False))
print(f"\n상관계수: 30명 표본 r={cor_small:.3f} / 900명 전체 r={cor_full:.3f}")
print("주의: r은 관계의 방향·정도를 말할 뿐, 원인을 증명하지 않습니다.")

# %% [markdown]
# ## 6. 시각화: 학년별 평균 / 산점도 / 스몰·전체 비교
# 차트를 PNG로 저장하고 코랩 화면에도 표시합니다.

# %%
plt.rcParams.update({"figure.dpi": 115, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(9.2, 4.6))
x = np.arange(len(by_grade))
ax.bar(x-0.19, by_grade.mean_sns_minutes/60, 0.36, label="SNS hours/day", color="#8B5CF6")
ax.bar(x+0.19, by_grade.mean_sleep_minutes/60, 0.36, label="Sleep hours/night", color="#16A6A6")
ax.set_xticks(x, [f"Grade {int(v)}" for v in by_grade.grade])
ax.set_ylabel("Hours")
ax.set_title("SNS use and sleep by school grade (synthetic survey)", weight="bold")
ax.grid(axis="y", alpha=0.14); ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "chart_grade_means.png", bbox_inches="tight")
plt.show(); plt.close(fig)

fig, ax = plt.subplots(figsize=(9.2, 4.7))
for grade, color in [(1,"#8B5CF6"),(2,"#00A5A1"),(3,"#FC7895")]:
    part = clean[clean.grade == grade]
    ax.scatter(part.sns_minutes/60, part.sleep_minutes/60, s=11, alpha=.33, label=f"Grade {grade}", color=color)
a,b = np.polyfit(clean.sns_minutes/60, clean.sleep_minutes/60, 1)
xs = np.array([0,9]); ax.plot(xs,a*xs+b,"--",color="#1E293B",linewidth=2,label="Simple trend")
ax.set(xlabel="SNS hours/day", ylabel="Sleep hours/night", xlim=(0,9.3), ylim=(3,11),
       title="SNS vs. sleep: correlation is not causation")
ax.legend(frameon=False); ax.grid(alpha=.12)
fig.tight_layout(); fig.savefig(OUTPUT_DIR / "chart_scatter.png", bbox_inches="tight")
plt.show(); plt.close(fig)

# %% [markdown]
# ## 7. AI 예측: 선형회귀 모델로 4주 가상 시나리오 비교
# 사용하는 변수: 일일 SNS 시간, 학년, 밤 10시 이후 SNS 사용 여부(Y/N).
# 데이터 80%로 학습하고 나머지 20%에서 MAE(평균절대오차, 분)를 구합니다.
# 
# **매우 중요:** 한 번 측정한 가상 설문만으로 실제 미래의 변화를 예언할 수 없습니다.
# 여기서 미래예측은 **'사용 시간이 매주 15분 늘어난다면?'** 하는 조건부 계산입니다.

# %%
def features(df):
    return pd.DataFrame({
        "sns_hours": pd.to_numeric(df.sns_minutes) / 60,
        "grade2": (pd.to_numeric(df.grade) == 2).astype(int),
        "grade3": (pd.to_numeric(df.grade) == 3).astype(int),
        "late": df.late_night_sns.astype(str).str.upper().eq("Y").astype(int)
    }, index=df.index)


def train_evaluate(df):
    x = features(df)
    y = df.sleep_minutes.astype(float)
    idx_train, idx_test = train_test_split(np.arange(len(df)), test_size=.2, random_state=21,
                                          stratify=df.grade)
    m = LinearRegression()
    m.fit(x.iloc[idx_train], y.iloc[idx_train])
    predicted = m.predict(x.iloc[idx_test])
    mae = mean_absolute_error(y.iloc[idx_test], predicted)
    r2 = r2_score(y.iloc[idx_test], predicted)
    m.fit(x, y)  # 시나리오 계산용 모델은 모든 데이터를 다시 학습
    return m, float(mae), float(r2)

model_small, mae_small, r2_small = train_evaluate(small)
model_full, mae_full, r2_full = train_evaluate(clean)
print(f"30명 표본 - 테스트 MAE: {mae_small:.1f}분, R²: {r2_small:.3f}")
print(f"900명 전체 - 테스트 MAE: {mae_full:.1f}분, R²: {r2_full:.3f}")
print("R²는 분할 표본에 민감하며, 작은 표본이 반드시 더 나쁘다는 뜻은 아닙니다.")

base_sns_minutes = 180
weekly_delta_minutes = 15
scenario = pd.DataFrame({
    "week": list(range(5)), "grade": [2]*5,
    "sns_minutes": [base_sns_minutes + i * weekly_delta_minutes for i in range(5)],
    "late_night_sns": ["Y"]*5
})
scenario["predicted_sleep_minutes"] = np.clip(model_full.predict(features(scenario)), 180, 720).round(1)
scenario["predicted_sleep_hours"] = (scenario.predicted_sleep_minutes/60).round(2)
scenario.to_csv(OUTPUT_DIR/"sns_sleep_future_scenario.csv",index=False,encoding="utf-8-sig")
print("\n학년 2 · 22시 이후 SNS=Y · 매주 +15분 가상 시나리오")
print(scenario.to_string(index=False))

fig, ax = plt.subplots(figsize=(9.2,4.4))
ax.plot(scenario.week,scenario.predicted_sleep_minutes/60,"-o",color="#8B5CF6",linewidth=3)
ax.set_xticks(scenario.week, [f"Week {v}" for v in scenario.week])
ax.set(ylabel="Predicted sleep hours/night",title="What-if scenario: SNS +15 min each week (not a causal forecast)")
ax.grid(alpha=.16)
fig.tight_layout();fig.savefig(OUTPUT_DIR /"chart_future_scenario.png",bbox_inches="tight")
plt.show();plt.close(fig)

# %% [markdown]
# ## 8. 결과: 인포그래픽 HTML 자동 생성
# 보고서 HTML은 그래프와 분석 수치를 내장한 **오프라인 파일**입니다.
# 파일을 두 번 클릭하면 Chrome/Edge에서 실행됩니다.

# %%
from datetime import datetime
import base64

def as_data_uri(path):
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode("ascii")

mean_sns = clean.sns_minutes.mean()/60
mean_sleep = clean.sleep_minutes.mean()/60
ratio_under7 = (clean.sleep_minutes<420).mean()*100
scenario_change = float((scenario.predicted_sleep_minutes.iloc[-1]-scenario.predicted_sleep_minutes.iloc[0]))
rows_grade = "".join(f"<tr><td><b>{int(r.grade)}학년</b></td><td>{int(r.students)}명</td>"
            f"<td>{r.mean_sns_minutes/60:.2f}시간</td><td>{r.mean_sleep_minutes/60:.2f}시간</td>"
            f"<td>{r.share_sleep_under7:.1f}%</td></tr>" for r in by_grade.itertuples(index=False))
html_report = f"""<!doctype html><html lang='ko'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>SNS×SLEEP | 학년별 데이터 리포트</title>
<style>
:root{{--bg:#0e1028;--panel:#1b1f3d;--ink:#f6f5ff;--muted:#bfc3de;--accent:#c6a5ff;--mint:#70e5d3}}
*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,'Malgun Gothic',sans-serif;background:var(--bg);color:var(--ink)}}
.wrap{{max-width:1170px;margin:auto;padding:32px 24px 90px}}.nav{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #3b4163;padding-bottom:24px;font-weight:850;letter-spacing:.06em}}.nav span{{font-size:12px;font-weight:600;color:var(--muted)}}
.hero{{padding:60px 0 40px}}.eyebrow{{font-size:13px;font-weight:800;letter-spacing:.15em;color:var(--mint)}}
h1{{font-size:clamp(36px,7vw,72px);letter-spacing:-.06em;line-height:1.13;margin:20px 0}}.lead{{font-size:17px;color:var(--muted);max-width:750px;line-height:1.8}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.kpi,.panel{{background:var(--panel);border:1px solid #313653;border-radius:18px;padding:23px}}.kpi .cap{{color:var(--muted);font-size:13px}}.kpi .value{{font-size:35px;font-weight:850;letter-spacing:-.04em;margin:8px 0}}.kpi small{{color:#a9afcd}}.big{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:20px}}
.panel h2{{font-size:21px;letter-spacing:-.035em;margin:0 0 10px}}.panel p{{color:var(--muted);font-size:13px;line-height:1.65}}.panel img{{width:100%;height:auto;border-radius:12px;background:#fff;margin-top:7px}}
.section{{font-weight:850;color:var(--mint);font-size:12px;letter-spacing:.1em;margin:54px 0 15px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:15px 12px;border-bottom:1px solid #3c4260;text-align:left}}th{{font-size:12px;color:var(--muted);font-weight:750}}td{{font-size:14px}}.note{{border-left:3px solid var(--mint);padding:5px 16px;color:#d6d9ec;line-height:1.8;margin-top:32px;background:#202645}}
footer{{color:#9fa6c6;font-size:12px;margin-top:36px}}@media(max-width:760px){{.grid,.big{{grid-template-columns:1fr 1fr}}}}@media(max-width:520px){{.grid,.big{{grid-template-columns:1fr}}h1{{font-size:39px}}}}
</style></head><body><div class='wrap'><div class='nav'>SNS / SLEEP LAB <span>EDUCATIONAL DEMO · SYNTHETIC DATA</span></div>
<div class='hero'><div class='eyebrow'>OUR SCHOOL · GRADE 1–3 · DATA REPORT</div>
<h1>스크롤하는 시간과<br>잠드는 시간의 관계.</h1>
<p class='lead'>가상 학교 1·2·3학년의 익명 합성 설문을 분석한 특강용 인포그래픽이다. 
실제 학교 조사 결과가 아니며 개인을 식별하는 정보는 포함하지 않는다.</p></div>
<div class='grid'>
<div class='kpi'><div class='cap'>분석에 사용한 가상 응답</div><div class='value'>{len(clean):,}<small>명</small></div><small>30명 표본과 비교</small></div>
<div class='kpi'><div class='cap'>하루 SNS 평균</div><div class='value'>{mean_sns:.1f}<small>시간</small></div><small>주중 하루 기준</small></div>
<div class='kpi'><div class='cap'>주중 수면 평균</div><div class='value'>{mean_sleep:.1f}<small>시간</small></div><small>1박 기준</small></div>
<div class='kpi'><div class='cap'>상관계수 (r)</div><div class='value'>{cor_full:+.2f}</div><small>원인·결과 판단 금지</small></div>
</div>
<div class='section'>01 / 학년별 데이터 비교</div>
<div class='big'><article class='panel'><h2>학년별 평균 능력치가 아니라 생활시간</h2><p>SNS 사용시간과 수면시간을 동일한 ‘시간’ 단위로 비교한다.</p><img alt='학년별 SNS 수면 평균 막대그래프' src='{as_data_uri(OUTPUT_DIR/'chart_grade_means.png')}'></article>
<article class='panel'><h2>하나의 점은 하나의 가상 응답</h2><p>아래 산점도에서 전체적인 기울기를 살펴보고 인과관계를 단정하지 않는다.</p><img alt='SNS와 수면의 산점도' src='{as_data_uri(OUTPUT_DIR/'chart_scatter.png')}'></article></div>
<div class='section'>02 / 학년별 상세 수치</div><article class='panel'><table><thead><tr><th>학년</th><th>응답 수</th><th>SNS 평균</th><th>수면 평균</th><th>7시간 미만 비율*</th></tr></thead><tbody>{rows_grade}</tbody></table><p>* 7시간은 수업 중 비율 비교용으로 설정한 구분값이며 의학적 진단이 아니다.</p></article>
<div class='section'>03 / 스몰데이터와 전체 데이터</div><div class='big'>
<article class='panel'><h2>30명 표본</h2><div style='font-size:44px;font-weight:900;color:#c6a5ff'>{cor_small:+.2f}</div><p>상관계수 r · 예측 모델 테스트 MAE {mae_small:.1f}분 · 표본 30개</p></article>
<article class='panel'><h2>900명 전체</h2><div style='font-size:44px;font-weight:900;color:#70e5d3'>{cor_full:+.2f}</div><p>상관계수 r · 예측 모델 테스트 MAE {mae_full:.1f}분 · 표본 900개</p></article></div>
<div class='section'>04 / 미래 ‘시나리오’ 예측</div><div class='big'><article class='panel'><h2>매주 SNS가 15분 증가하면?</h2><p>2학년, 밤 10시 이후 SNS 이용 Y를 고정한 <b>조건부</b> 시뮬레이션.</p>
<img alt='4주 가상 시나리오 선그래프' src='{as_data_uri(OUTPUT_DIR/'chart_future_scenario.png')}'></article>
<article class='panel'><h2>4주 후 계산된 변화</h2><div style='font-size:46px;font-weight:900;color:#c6a5ff'>{scenario_change:+.1f}<small style='font-size:18px'>분</small></div>
<p>입력 SNS시간이 주 15분씩 달라지는 가정에서 회귀모델이 출력하는 차이. 개인의 실제 수면 변화가 아니라 모형의 예측값이다.</p><p>다음엔 ‘늦은 밤 SNS를 하지 않는다면?’, ‘학년이 바뀌면?’을 함께 비교해 보자.</p></article></div>
<div class='note'><b>안전한 해석:</b> 본 데이터는 2026년 강의용으로 만든 가상 익명 데이터이다. 상관관계는 인과관계가 아니다. 단면 설문만으로 실제 미래 변화를 예언할 수 없으며, 개인 건강 판정·상담에 사용해서는 안 된다.</div>
<footer>EDUCATIONAL SYNTHETIC DATASET · CREATED WITH PYTHON · OFFLINE HTML INFOGRAPHIC</footer>
</div></body></html>"""
report_path = OUTPUT_DIR / "sns_sleep_infographic.html"
report_path.write_text(html_report,encoding="utf-8")
print("인포그래픽 생성:",report_path)

# %% [markdown]
# ## 9. 다운로드: 모든 결과 ZIP으로 묶기
# Colab에서는 다음 셀을 실행하면 ZIP 다운로드가 시작됩니다.
# ```
# SNS_SLEEP_실습결과/
#   sns_sleep_survey_source.html     <- 크롤링 대상 가상 웹페이지
#   sns_sleep_raw.csv                <- 수집 원본
#   sns_sleep_clean.csv              <- 전처리 완료
#   sns_sleep_small30.csv            <- 학년별 10명 표본
#   sns_sleep_grade_summary.csv      <- 학년별 통계
#   sns_sleep_future_scenario.csv    <- 4주 예측
#   sns_sleep_infographic.html       <- 최종 인포그래픽
#   chart_*.png                      <- 시각화 이미지
# ```

# %%
zip_path = Path.cwd() / "SNS_SLEEP_Colab_실습결과.zip"
with ZipFile(zip_path,"w",ZIP_DEFLATED) as z:
    for f in OUTPUT_DIR.iterdir():
        if f.is_file():
            z.write(f,arcname=f.name)
print("압축 파일 생성 완료:",zip_path.name, "| 내부 파일", len(list(OUTPUT_DIR.iterdir())),"개")
if "google.colab" in sys.modules:
    from google.colab import files
    files.download(str(zip_path))
