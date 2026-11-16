#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DEX/LAB | Google Colab 또는 Python 3에서 실행할 수 있는 포켓몬 데이터 파이프라인.
수집(requests+BeautifulSoup), CSV, 정제(pandas), 분석, KNN 예측, 오프라인 HTML 결과.
크롤링 실패 시 예비 표본을 사용하며, 이것을 실시간 수집으로 표기하지 않습니다.
"""


# ----- 실습 코드 1 -----
import io
import os
import re
import sys
import html
import zipfile
from pathlib import Path

import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from IPython.display import display
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

URL = "https://pokemondb.net/pokedex/all"
RAW_FILE = "pokemon_collected_raw.csv"
CLEAN_FILE = "pokemon_clean.csv"
SMALL_FILE = "pokemon_small30.csv"
REPORT_FILE = "pokemon_report.html"

COLUMNS = ["번호", "이름", "타입1", "타입2", "총합", "HP", "공격", "방어", "특수공격", "특수방어", "스피드", "폼"]
NUM_COLS = ["번호", "총합", "HP", "공격", "방어", "특수공격", "특수방어", "스피드"]
FEATURES = ["HP", "공격", "방어", "특수공격", "특수방어"]
GEN_LIMITS = [151, 251, 386, 493, 649, 721, 809, 905, 1025]
try:
    from google.colab import files as colab_files
    IS_COLAB = True
except ImportError:
    IS_COLAB = False
PLOT_INLINE = False  # Python CLI는 HTML 파일에만 그래프 저장
print("[준비 완료] Python 분석 도구를 불러왔습니다.")

# ----- 실습 코드 2 -----
# 사이트 장애·차단 상황에서도 모든 셀을 실행할 수 있도록 포함된 수업용 예비 데이터입니다.
# 내용: 공개 도감에서 확인한 1~9세대 스타터 계열·유명 포켓몬 및 중복 폼 2개.
FALLBACK_CSV = '번호,이름,타입1,타입2,총합,HP,공격,방어,특수공격,특수방어,스피드,폼\n1,Bulbasaur,Grass,Poison,318,45,49,49,65,65,45,기본\n2,Ivysaur,Grass,Poison,405,60,62,63,80,80,60,기본\n3,Venusaur,Grass,Poison,525,80,82,83,100,100,80,기본\n4,Charmander,Fire,,309,39,52,43,60,50,65,기본\n5,Charmeleon,Fire,,405,58,64,58,80,65,80,기본\n6,Charizard,Fire,Flying,534,78,84,78,109,85,100,기본\n6,Charizard,Fire,Dragon,634,78,130,111,130,85,100,Mega Charizard X\n7,Squirtle,Water,,314,44,48,65,50,64,43,기본\n8,Wartortle,Water,,405,59,63,80,65,80,58,기본\n9,Blastoise,Water,,530,79,83,100,85,105,78,기본\n25,Pikachu,Electric,,320,35,55,40,50,50,90,기본\n26,Raichu,Electric,,485,60,90,55,90,80,110,기본\n132,Ditto,Normal,,288,48,48,48,48,48,48,기본\n133,Eevee,Normal,,325,55,55,50,45,65,55,기본\n135,Jolteon,Electric,,525,65,65,60,110,95,130,기본\n150,Mewtwo,Psychic,,680,106,110,90,154,90,130,기본\n151,Mew,Psychic,,600,100,100,100,100,100,100,기본\n152,Chikorita,Grass,,318,45,49,65,49,65,45,기본\n153,Bayleef,Grass,,405,60,62,80,63,80,60,기본\n154,Meganium,Grass,,525,80,82,100,83,100,80,기본\n155,Cyndaquil,Fire,,309,39,52,43,60,50,65,기본\n156,Quilava,Fire,,405,58,64,58,80,65,80,기본\n157,Typhlosion,Fire,,534,78,84,78,109,85,100,기본\n158,Totodile,Water,,314,50,65,64,44,48,43,기본\n159,Croconaw,Water,,405,65,80,80,59,63,58,기본\n160,Feraligatr,Water,,530,85,105,100,79,83,78,기본\n252,Treecko,Grass,,310,40,45,35,65,55,70,기본\n253,Grovyle,Grass,,405,50,65,45,85,65,95,기본\n254,Sceptile,Grass,,530,70,85,65,105,85,120,기본\n255,Torchic,Fire,,310,45,60,40,70,50,45,기본\n256,Combusken,Fire,Fighting,405,60,85,60,85,60,55,기본\n257,Blaziken,Fire,Fighting,530,80,120,70,110,70,80,기본\n258,Mudkip,Water,,310,50,70,50,50,50,40,기본\n259,Marshtomp,Water,Ground,405,70,85,70,60,70,50,기본\n260,Swampert,Water,Ground,535,100,110,90,85,90,60,기본\n387,Turtwig,Grass,,318,55,68,64,45,55,31,기본\n388,Grotle,Grass,,405,75,89,85,55,65,36,기본\n389,Torterra,Grass,Ground,525,95,109,105,75,85,56,기본\n390,Chimchar,Fire,,309,44,58,44,58,44,61,기본\n391,Monferno,Fire,Fighting,405,64,78,52,78,52,81,기본\n392,Infernape,Fire,Fighting,534,76,104,71,104,71,108,기본\n393,Piplup,Water,,314,53,51,53,61,56,40,기본\n394,Prinplup,Water,,405,64,66,68,81,76,50,기본\n395,Empoleon,Water,Steel,530,84,86,88,111,101,60,기본\n495,Snivy,Grass,,308,45,45,55,45,55,63,기본\n496,Servine,Grass,,413,60,60,75,60,75,83,기본\n497,Serperior,Grass,,528,75,75,95,75,95,113,기본\n498,Tepig,Fire,,308,65,63,45,45,45,45,기본\n499,Pignite,Fire,Fighting,418,90,93,55,70,55,55,기본\n500,Emboar,Fire,Fighting,528,110,123,65,100,65,65,기본\n501,Oshawott,Water,,308,55,55,45,63,45,45,기본\n502,Dewott,Water,,413,75,75,60,83,60,60,기본\n503,Samurott,Water,,528,95,100,85,108,70,70,기본\n650,Chespin,Grass,,313,56,61,65,48,45,38,기본\n651,Quilladin,Grass,,405,61,78,95,56,58,57,기본\n652,Chesnaught,Grass,Fighting,530,88,107,122,74,75,64,기본\n653,Fennekin,Fire,,307,40,45,40,62,60,60,기본\n654,Braixen,Fire,,409,59,59,58,90,70,73,기본\n655,Delphox,Fire,Psychic,534,75,69,72,114,100,104,기본\n656,Froakie,Water,,314,41,56,40,62,44,71,기본\n657,Frogadier,Water,,405,54,63,52,83,56,97,기본\n658,Greninja,Water,Dark,530,72,95,67,103,71,122,기본\n722,Rowlet,Grass,Flying,320,68,55,55,50,50,42,기본\n723,Dartrix,Grass,Flying,420,78,75,75,70,70,52,기본\n724,Decidueye,Grass,Ghost,530,78,107,75,100,100,70,기본\n725,Litten,Fire,,320,45,65,40,60,40,70,기본\n726,Torracat,Fire,,420,65,85,50,80,50,90,기본\n727,Incineroar,Fire,Dark,530,95,115,90,80,90,60,기본\n728,Popplio,Water,,320,50,54,54,66,56,40,기본\n729,Brionne,Water,,420,60,69,69,91,81,50,기본\n730,Primarina,Water,Fairy,530,80,74,74,126,116,60,기본\n810,Grookey,Grass,,310,50,65,50,40,40,65,기본\n811,Thwackey,Grass,,420,70,85,70,55,60,80,기본\n812,Rillaboom,Grass,,530,100,125,90,60,70,85,기본\n813,Scorbunny,Fire,,310,50,71,40,40,40,69,기본\n814,Raboot,Fire,,420,65,86,60,55,60,94,기본\n815,Cinderace,Fire,,530,80,116,75,65,75,119,기본\n816,Sobble,Water,,310,50,40,40,70,40,70,기본\n817,Drizzile,Water,,420,65,60,55,95,55,90,기본\n818,Inteleon,Water,,530,70,85,65,125,65,120,기본\n906,Sprigatito,Grass,,310,40,61,54,45,45,65,기본\n907,Floragato,Grass,,410,61,80,63,60,63,83,기본\n908,Meowscarada,Grass,Dark,530,76,110,70,81,70,123,기본\n909,Fuecoco,Fire,,310,67,45,59,63,40,36,기본\n910,Crocalor,Fire,,411,81,55,78,90,58,49,기본\n911,Skeledirge,Fire,Ghost,530,104,75,100,110,75,66,기본\n912,Quaxly,Water,,310,55,65,45,50,45,50,기본\n913,Quaxwell,Water,,410,70,85,65,65,60,65,기본\n914,Quaquaval,Water,Fighting,530,85,120,80,85,75,85,기본\n150,Mewtwo,Psychic,,780,106,190,100,154,100,130,Mega Mewtwo X\n'

def scrape_pokedex(url=URL):
    """Pokémon Database의 공개 HTML 테이블을 한 번 읽어 표 형태로 반환합니다."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SchoolDataWorkshop/1.0; educational single-page request)"}
    response = requests.get(url, headers=headers, timeout=(6, 15))
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    records = []
    for tr in soup.select("table#pokedex tbody tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 10:
            continue
        found = re.search(r"\d+", cells[0].get_text(" ", strip=True))
        if not found:
            continue
        name_tag = cells[1].select_one("a.ent-name") or cells[1].find("a")
        if name_tag is None:
            continue
        name = name_tag.get_text(" ", strip=True)
        full_label = cells[1].get_text(" ", strip=True)
        form = full_label.replace(name, "", 1).strip() or "기본"
        types = [a.get_text(strip=True) for a in cells[2].find_all("a")]
        if not types:
            continue
        try:
            values = [int(re.sub(r"[^0-9]", "", c.get_text(strip=True))) for c in cells[3:10]]
        except ValueError:
            continue
        if len(values) != 7:
            continue
        records.append([int(found.group()), name, types[0], types[1] if len(types)>1 else "", *values, form])
    if len(records) < 500:
        raise ValueError(f"페이지 구조가 변경되었거나 충분한 행을 추출하지 못했습니다: {len(records)}행")
    return pd.DataFrame(records, columns=COLUMNS)

try:
    if os.environ.get("POKE_LAB_OFFLINE") == "1":
        raise ConnectionError("오프라인 실습 모드")
    df_raw = scrape_pokedex()
    data_source = "실시간 웹 크롤링"
except (requests.RequestException, ConnectionError, ValueError, IndexError) as err:
    print("[수집 실패]", str(err)[:160])
    print("[대체 데이터] 수업용 내장 샘플 90행을 사용합니다. 실시간 수집 자료가 아닙니다.")
    df_raw = pd.read_csv(io.StringIO(FALLBACK_CSV))
    data_source = "수업용 검증 샘플 (실시간 수집 아님)"

# CSV 인코딩 utf-8-sig: Windows Excel에서도 한글 열 이름을 쉽게 확인할 수 있습니다.
df_raw.to_csv(RAW_FILE, index=False, encoding="utf-8-sig")
print(f"수집 상태: {data_source} / 원자료: {len(df_raw):,}행 / 파일: {RAW_FILE}")
display(df_raw.head(8))

# ----- 실습 코드 3 -----
df_check = pd.read_csv(RAW_FILE, encoding="utf-8-sig")
print("CSV 재읽기 성공:", len(df_check), "행")
print("열 이름:", ", ".join(df_check.columns))
display(df_check.head(5))

# ----- 실습 코드 4 -----
def generation_of(number):
    for index, limit in enumerate(GEN_LIMITS, start=1):
        if number <= limit:
            return index
    return np.nan  # 1~9세대 이후 데이터는 자동으로 10세대라고 단정하지 않습니다.

def preprocess(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    before = len(df)
    for c in NUM_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["번호", "이름", "타입1", "총합", *FEATURES, "스피드"])
    df = df[(df[NUM_COLS] >= 0).all(axis=1)]
    df = df.sort_values("번호", kind="stable").drop_duplicates(subset=["번호"], keep="first")
    stat_sum = df[[*FEATURES, "스피드"]].sum(axis=1)
    df = df[df["총합"].eq(stat_sum)].copy()
    df["번호"] = df["번호"].astype(int)
    df["세대"] = df["번호"].map(generation_of)
    df["폼"] = df["폼"].fillna("기본") if "폼" in df.columns else "기본"
    df = df.sort_values("번호").reset_index(drop=True)
    return df, before

df_clean, before_count = preprocess(RAW_FILE)
df_clean.to_csv(CLEAN_FILE, index=False, encoding="utf-8-sig")
print(f"처리: 원본 {before_count:,}행 → 정제 {len(df_clean):,}행 / 제거 {before_count-len(df_clean):,}행")
assert len(df_clean) >= 15, "표본이 너무 적습니다."
display(df_clean.head(8))

# ----- 실습 코드 5 -----
df_small = (df_clean.assign(_sample_rank=(df_clean["번호"] * 2654435761) % (2**32))
            .sort_values(["_sample_rank", "번호"]).head(30).drop(columns="_sample_rank").sort_values("번호"))
df_small.to_csv(SMALL_FILE, index=False, encoding="utf-8-sig")

def metrics(df, label):
    return {"규모":label,"데이터 수":len(df),"평균 스피드":round(df["스피드"].mean(),1),
            "평균 총합":round(df["총합"].mean(),1),"스피드 100 이상":int((df["스피드"]>=100).sum())}

summary = pd.DataFrame([metrics(df_small, "스몰데이터"), metrics(df_clean, "전체 데이터")])
display(summary)
print("\n[타입1 기준 평균 스피드 TOP 10]")
type_report = (df_clean.groupby("타입1", as_index=False).agg(마릿수=("번호","count"), 평균스피드=("스피드","mean"))
               .sort_values("평균스피드",ascending=False))
display(type_report.head(10).round(1))
print("\n[스피드 TOP 10]")
display(df_clean.nlargest(10,"스피드")[["번호","이름","타입1","공격","스피드"]])

# ----- 실습 코드 6 -----
fig_top = px.bar(df_clean.nlargest(12, "스피드").sort_values("스피드"),
    x="스피드", y="이름", orientation="h", color="스피드", color_continuous_scale="Viridis",
    title="스피드 TOP 12", text="스피드")
fig_top.update_layout(template="plotly_dark",height=490,margin=dict(t=70,b=40,l=30,r=30))
if PLOT_INLINE: fig_top.show()

fig_scatter = px.scatter(df_clean, x="공격", y="스피드", color="타입1", hover_name="이름",
    hover_data=["세대", "총합"], title="공격력이 높으면 스피드도 높을까?", opacity=.78)
fig_scatter.update_layout(template="plotly_dark", height=465)
if PLOT_INLINE: fig_scatter.show()

by_generation = (df_clean.dropna(subset=["세대"]).groupby("세대",as_index=False)
                 .agg(평균스피드=("스피드","mean"), 개수=("번호","count")))
fig_generation = px.line(by_generation, x="세대",y="평균스피드",markers=True,
    title="세대별 평균 스피드 (편의표본/데이터 구성에 주의)")
fig_generation.update_layout(template="plotly_dark",height=390)
if PLOT_INLINE: fig_generation.show()

# ----- 실습 코드 7 -----
def evaluate_knn(df, name):
    X = df[FEATURES].astype(float)
    y = df["스피드"].astype(float)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.25, random_state=42)
    model = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=min(5,len(X_train))))
    model.fit(X_train, y_train)
    mae = mean_absolute_error(y_test, model.predict(X_test))
    return round(mae,2)

mae_small = evaluate_knn(df_small, "스몰")
mae_all = evaluate_knn(df_clean, "전체")
print(f"스몰데이터({len(df_small)}행) 스피드 예측 평균절대오차 MAE: {mae_small:.2f}")
print(f"전체 데이터({len(df_clean)}행) 스피드 예측 평균절대오차 MAE: {mae_all:.2f}")
print("주의: 스몰/전체의 평가 집합이 서로 다르므로 MAE 직접 비교는 탐색적인 참고 자료입니다.")

# 아래 다섯 숫자를 자유롭게 바꾸어 나만의 신규 캐릭터를 만들어 보세요.
NEW_MONSTER = {"HP": 78, "공격": 95, "방어": 76, "특수공격": 105, "특수방어": 82}
model_all = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=min(5,len(df_clean))))
model_all.fit(df_clean[FEATURES], df_clean["스피드"])
new_df = pd.DataFrame([NEW_MONSTER],columns=FEATURES)
new_pred = float(model_all.predict(new_df)[0])
print(f"\n가상의 신규 캐릭터 예상 스피드: 약 {new_pred:.1f} (실제 신작 정보가 아닌 교육용 예측)")

# 가장 유사한 다섯 캐릭터를 함께 출력합니다.
scaler = model_all.named_steps["standardscaler"]
knn = model_all.named_steps["kneighborsregressor"]
dists, ix = knn.kneighbors(scaler.transform(new_df))
display(df_clean.iloc[ix[0]][["이름","HP","공격","방어","특수공격","특수방어","스피드"]])

# ----- 실습 코드 8 -----
forecast_10 = None
if len(df_clean) >= 500 and len(by_generation) == 9:
    lr = LinearRegression().fit(by_generation[["세대"]], by_generation["평균스피드"])
    forecast_10 = max(1.,min(200.,float(lr.predict(pd.DataFrame({"세대":[10]}))[0])))
    print(f"가상 10세대 평균 스피드 추세 추정: 약 {forecast_10:.1f}")
    print("※ 과거 세대 평균 9개를 직선 연장한 추정치일 뿐, 출시 예정 능력치가 아닙니다.")
else:
    print("10세대 평균 추정 생략: 전체 도감에 해당하는 충분한 자료가 필요합니다.")
print("미래예측 체험은 위의 '가상 신규 캐릭터 스피드'에서 이미 수행할 수 있습니다.")

# ----- 실습 코드 9 -----
fig_top.update_layout(paper_bgcolor="#11162a", plot_bgcolor="#11162a",font=dict(color="#ecf2ff"))
fig_scatter.update_layout(paper_bgcolor="#11162a", plot_bgcolor="#11162a",font=dict(color="#ecf2ff"))
fig_generation.update_layout(paper_bgcolor="#11162a", plot_bgcolor="#11162a",font=dict(color="#ecf2ff"))
chart1 = pio.to_html(fig_top, full_html=False, include_plotlyjs=True, config={"responsive":True})
chart2 = pio.to_html(fig_scatter, full_html=False, include_plotlyjs=False, config={"responsive":True})
chart3 = pio.to_html(fig_generation, full_html=False, include_plotlyjs=False, config={"responsive":True})
forecast_line = (f"가상 10세대 평균 스피드 약 {forecast_10:.1f} (참고용 추세 추정)" if forecast_10 is not None
                 else "10세대 수치 추정은 충분한 전체 데이터에서만 제공")
report_html = f"""<!DOCTYPE html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>DEX/LAB 포켓몬 데이터 분석 결과</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#090c19;color:#ecf2ff;font-family:system-ui,'Malgun Gothic',sans-serif}}
main{{max-width:1150px;margin:auto;padding:45px 25px}}h1{{font-size:clamp(36px,6vw,70px);margin:15px 0}}h2{{font-size:23px}}
small, .muted{{color:#abb9d5}}.eyebrow{{color:#73e9c0;letter-spacing:3px;font-weight:800}}.lead{{font-size:17px;line-height:1.8;color:#bbcbe5}}
.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:13px;margin:30px 0}}.metric,.panel{{border:1px solid #2b3553;background:#11162a;border-radius:18px;padding:21px}}.metric strong{{display:block;font-size:32px;color:#80e6fe;margin-top:9px}}
.panel{{margin:16px 0}}footer{{line-height:1.8;color:#b5c1d9;padding:30px 0}}
</style></head><body><main><div class='eyebrow'>DEX//LAB — BIG DATA × SMALL DATA</div>
<h1>캐릭터의 능력치를<br>데이터로 읽다.</h1><p class='lead'>수집 → CSV 저장 → 전처리 → 분석 → 예측 · 실습 데이터: {html.escape(data_source)}</p>
<div class='metrics'><div class='metric'>정제 데이터<strong>{len(df_clean):,}</strong>마리</div><div class='metric'>스몰데이터<strong>{len(df_small):,}</strong>마리</div><div class='metric'>평균 스피드<strong>{df_clean['스피드'].mean():.1f}</strong>포인트</div><div class='metric'>AI 예상 스피드<strong>{new_pred:.1f}</strong>포인트</div></div>
<section class='panel'><h2>01 / 속도 순위</h2>{chart1}</section><section class='panel'><h2>02 / 공격력과 스피드의 관계</h2>{chart2}</section><section class='panel'><h2>03 / 세대별 스피드 변화</h2>{chart3}</section>
<section class='panel'><h2>04 / 미래예측 실험</h2><p class='lead'>가상 캐릭터 5개 능력치: {html.escape(str(NEW_MONSTER))}</p>
<p class='lead'>KNN 예측 스피드: <b>{new_pred:.1f}</b> · 스몰 MAE: {mae_small:.2f} · 전체 MAE: {mae_all:.2f}</p><p>{forecast_line}</p></section>
<footer>출처: <a href='{URL}' style='color:#73e9c0'>{URL}</a><br>예측은 교육용 통계 추정이며 실제 출시 게임 캐릭터의 능력치가 아닙니다. 표본은 대표성이 없을 수 있습니다.</footer>
</main></body></html>"""
Path(REPORT_FILE).write_text(report_html, encoding="utf-8")
print(f"보고서 저장: {REPORT_FILE} ({Path(REPORT_FILE).stat().st_size//1024:,} KB) — 그래프 포함 독립형 HTML")

# ----- 실습 코드 10 -----
ZIP_NAME = "DEX_LAB_Colab_결과물.zip"
with zipfile.ZipFile(ZIP_NAME,"w",compression=zipfile.ZIP_DEFLATED) as z:
    for f in [RAW_FILE,CLEAN_FILE,SMALL_FILE,REPORT_FILE]:
        z.write(f)
print(f"최종 결과물: {ZIP_NAME} / 포함 파일 4개")
if False:  # CLI 모드에서는 Colab 노트북의 파일 다운로드 UI를 실행하지 않습니다.
    colab_files.download(ZIP_NAME)
else:
    print("Colab 이외 환경에서는 현재 디렉터리에서 ZIP 파일을 확인하세요.")
