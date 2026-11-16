# -*- coding: utf-8 -*-
"""Futsal AI game CSV → Python pandas/numpy analysis & three PNG figures.

Usage:
  python futsal_5v5_python_analysis.py futsal_5v5_ai_match_positions_sample.csv
  python futsal_5v5_python_analysis.py futsal_5v5_ai_match_positions.csv
"""
from pathlib import Path
import sys
CSV_PATH = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('futsal_5v5_ai_match_positions_sample.csv')
CSV_TEXT = CSV_PATH.read_text(encoding='utf-8-sig')
print('분석 대상 CSV:', CSV_PATH)


# === 01 · CSV 불러오기 및 전처리 ===
import io
import pandas as pd
import numpy as np

# HTML에서 업로드한 CSV 문자열을 Python으로 전달받는다.
raw_df = pd.read_csv(io.StringIO(CSV_TEXT.lstrip("\ufeff")))
required = ["game_time_sec", "team", "player_id", "x_m", "y_m"]
missing = [c for c in required if c not in raw_df.columns]
if missing:
    raise ValueError(f"필수 CSV 열이 없습니다: {missing}")

df = raw_df.copy()
for col in ["game_time_sec", "x_m", "y_m"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df["team"] = df["team"].astype(str).str.strip().str.upper()
df["player_id"] = df["player_id"].astype(str).str.strip().str.upper()

# 기존 풋살 게임은 40m × 20m 경기장에서 A1~A5, B1~B5를 기록한다.
df = df.dropna(subset=required)
df = df[df["x_m"].between(0, 40) & df["y_m"].between(0, 20)]
df = df[df["game_time_sec"] >= 0]
df = df[df["team"].isin(["A", "B"])]
df = df[df["player_id"].str.fullmatch(r"[AB][1-5]")]
df = df[df["player_id"].str[0] == df["team"]]
df = df.drop_duplicates(subset=["player_id", "game_time_sec"], keep="last")
df = df.sort_values(["player_id", "game_time_sec"]).reset_index(drop=True)
if "role" not in df.columns:
    df["role"] = "포지션 미상"
if "ball_owner" not in df.columns:
    df["ball_owner"] = 0
df["ball_owner"] = pd.to_numeric(df["ball_owner"], errors="coerce").fillna(0).astype(int)
if df.empty:
    raise ValueError("유효한 데이터가 없습니다. CSV 헤더와 좌표를 확인하세요.")
print(f"원본 {len(raw_df):,}행 → 정제 후 {len(df):,}행")
print(f"선수 {df['player_id'].nunique()}명 · 기록 종료 {df['game_time_sec'].max():.1f}초")
print(df[["game_time_sec", "team", "player_id", "x_m", "y_m"]].head(7).to_string(index=False))


# === 02 · 기초 통계와 선수별 기록 수 ===
basic = (df.groupby(["team", "player_id"], as_index=False)
         .agg(좌표수=("x_m", "size"),
              평균X=("x_m", "mean"), 평균Y=("y_m", "mean"),
              공소유_표본수=("ball_owner", "sum")))
print("[선수별 요약]")
print(basic.round(2).to_string(index=False))
print("\n[팀별 평균 위치]")
print(df.groupby("team")[["x_m", "y_m"]].mean().round(2).to_string())


# === 03 · 좌표로 추정 이동거리 계산 ===
def movement_table(frame):
    work = frame.sort_values(["player_id", "game_time_sec"]).copy()
    group = work.groupby("player_id", sort=False)
    dx = group["x_m"].diff().fillna(0)
    dy = group["y_m"].diff().fillna(0)
    dt = group["game_time_sec"].diff().fillna(0)
    # 2초를 초과하는 큰 데이터 공백은 이동거리 계산에서 제외한다.
    valid = (dt > 0) & (dt <= 2)
    work["step_m"] = np.where(valid, np.hypot(dx, dy), 0.0)
    work["interval_sec"] = np.where(valid, dt, 0.0)
    work["speed_mps"] = np.where(valid, work["step_m"] / dt.replace(0, np.nan), 0.0)
    return work

movement_df = movement_table(df)
distances = (movement_df.groupby(["team", "player_id"], as_index=False)
             .agg(추정거리m=("step_m", "sum"),
                  관측시간초=("interval_sec", "sum")))
distances["평균속도mps"] = (distances["추정거리m"] / distances["관측시간초"].replace(0, np.nan)).fillna(0)
print("[좌표 간 직선 연결로 계산한 추정 이동거리]")
print(distances.round(2).sort_values("추정거리m", ascending=False).to_string(index=False))
print("\n주의: 샘플 간 실제 곡선 이동은 재현할 수 없어 이동거리가 작게 추정될 수 있습니다.")


# === 04 · 팀별·공격 구역별 공간 분석 ===
zones_df = df.copy()
zones_df["공격방향X"] = np.where(zones_df["team"] == "A", zones_df["x_m"], 40 - zones_df["x_m"])
zones_df["활동구역"] = pd.cut(
    zones_df["공격방향X"],
    bins=[-0.001, 40/3, 80/3, 40.001],
    labels=["수비", "중앙", "공격"],
    include_lowest=True
)
zone_counts = (zones_df.groupby(["team", "활동구역"], observed=True)
               .size().unstack(fill_value=0))
print("[팀별 활동 구역 기록 수]")
print(zone_counts.to_string())
print("\n[팀별 공 소유로 기록된 위치 샘플 수]")
print(df.groupby("team")["ball_owner"].sum().to_string())
print("공 소유 표본 비율은 실제 공 점유율(시간)과 동일하지 않습니다.")


# === 05 · 히트맵·시간 그래프용 Python 분석 ===
import json

def build_dashboard(team="all", player="all", until=None):
    subset = df
    if team in ("A", "B"):
        subset = subset[subset["team"] == team]
    if player != "all":
        subset = subset[subset["player_id"] == player]
    if until is not None:
        subset = subset[subset["game_time_sec"] <= float(until)]
    subset = subset.copy()
    if subset.empty:
        return json.dumps({"empty": True, "rows": 0}, ensure_ascii=False)

    trajectory = movement_table(subset)
    roster = []
    for pid, grp in trajectory.groupby("player_id", sort=True):
        played = float(grp["interval_sec"].sum())
        meters = float(grp["step_m"].sum())
        roster.append({
            "id": str(pid), "team": str(pid)[0],
            "role": str(grp["role"].iloc[0]),
            "points": int(len(grp)), "distance": round(meters, 2),
            "avgSpeed": round(meters / played, 2) if played else 0.0,
            "possess": int(grp["ball_owner"].sum())
        })
    roster.sort(key=lambda x: x["distance"], reverse=True)

    teams = []
    for t in ["A", "B"]:
        seg = trajectory[trajectory["team"] == t]
        teams.append({"team": t, "rows": int(len(seg)),
                      "distance": round(float(seg["step_m"].sum()), 2),
                      "possess": int(seg["ball_owner"].sum())})

    # 누적 위치 밀도를 80 × 40 격자에 배치하고 가우시안 평활화한다.
    grid = np.histogram2d(subset["y_m"], subset["x_m"],
                          bins=[40, 80], range=[[0, 20], [0, 40]])[0]
    radius = np.arange(-5, 6)
    kernel = np.exp(-(radius**2) / (2 * 2.3**2))
    kernel = kernel / kernel.sum()
    grid = np.apply_along_axis(lambda v: np.convolve(v, kernel, mode="same"), 0, grid)
    grid = np.apply_along_axis(lambda v: np.convolve(v, kernel, mode="same"), 1, grid)
    peak = float(grid.max())
    if peak > 0:
        grid = grid / peak

    # 공격 방향을 통일한 수비 / 중앙 / 공격 구역
    oriented_x = np.where(subset["team"] == "A", subset["x_m"], 40 - subset["x_m"])
    sector = np.where(oriented_x < 40/3, 0, np.where(oriented_x < 80/3, 1, 2))
    zones = np.bincount(sector, minlength=3).tolist()

    # 12구간에 기록된 두 팀의 관측 이동거리 변화
    end_time = float(max(1, subset["game_time_sec"].max()))
    trajectory["bucket"] = np.minimum((trajectory["game_time_sec"] / end_time * 12).astype(int), 11)
    traces = {}
    for t in ("A", "B"):
        seg = trajectory[trajectory["team"] == t]
        sums = seg.groupby("bucket")["step_m"].sum()
        traces[t] = [round(float(sums.get(i, 0)), 1) for i in range(12)]

    latest = subset.sort_values("game_time_sec").groupby("player_id").tail(1)
    positions = [{"id": str(r.player_id), "x": float(r.x_m), "y": float(r.y_m)}
                 for r in latest.itertuples()]
    return json.dumps({
        "empty": False, "rows": int(len(subset)),
        "players": roster, "teams": teams,
        "time": round(float(subset["game_time_sec"].max()), 1),
        "distance": round(float(trajectory["step_m"].sum()), 1),
        "heat": {"w": 80, "h": 40, "values": np.round(grid, 3).flatten().tolist()},
        "zones": zones, "traces": traces, "positions": positions
    }, ensure_ascii=False)

print("Python 히트맵 및 시계열 분석 함수 준비 완료")
print("예: build_dashboard(team='A', player='A3', until=60)")


# === 06 · 분석 결과 해석하기 ===
result = json.loads(build_dashboard())
leader = result["players"][0]
print(f"전체 위치 기록: {result['rows']:,}건")
print(f"좌표 연결 기준 추정 총 이동거리: {result['distance']:,.1f}m")
print(f"최다 이동 선수: {leader['id']} ({leader['distance']:,.1f}m)")
print("\n탐구 질문:")
print("1. A팀과 B팀의 활동 분포는 어떤 차이가 있을까요?")
print("2. 골키퍼의 활동 범위가 좁은 이유는 무엇일까요?")
print("3. 좌표 간격을 0.42초에서 2초로 늘리면 계산한 거리는 어떻게 달라질까요?")
print("4. 좌표가 많다고 반드시 더 오래 달렸다고 말할 수 있을까요?")
print("\n주의: 생성형 자동 경기 데이터이며 실제 경기 기록이 아닙니다.")


# === 07 · 그래프 생성 및 파일 저장 ===
# 07. 그래프 생성: 선수별 추정 거리 / 풋살 히트맵 / 시간대별 이동거리
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle, Circle
from pathlib import Path

r = json.loads(build_dashboard())
fig, ax = plt.subplots(figsize=(11, 5.6))
names = [p["id"] for p in r["players"]][::-1]
values = [p["distance"] for p in r["players"]][::-1]
colors = ["#63aafa" if name.startswith("A") else "#ff9f60" for name in names]
ax.barh(names, values, color=colors)
ax.set_xlabel("Estimated distance from sampled positions (m)")
ax.set_title("5v5 Futsal: Estimated Player Travel Distance")
ax.grid(axis="x", alpha=0.15)
fig.tight_layout()
fig.savefig("futsal_player_distance.png", dpi=160)
plt.show()

# 40m x 20m 코트를 위에서 본 히트맵
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_facecolor("#2b8048")
ax.add_patch(Rectangle((0, 0), 40, 20, fill=False, edgecolor="white", linewidth=2))
ax.plot([20, 20], [0, 20], color="white", lw=1.5)
ax.add_patch(Circle((20, 10), 3, fill=False, ec="white", lw=1.5))
ax.add_patch(Rectangle((0, 5), 6, 10, fill=False, edgecolor="white"))
ax.add_patch(Rectangle((34, 5), 6, 10, fill=False, edgecolor="white"))
heat = np.array(r["heat"]["values"]).reshape(r["heat"]["h"], r["heat"]["w"])
colors = LinearSegmentedColormap.from_list("futsal", ["#175bc5", "#55cbf0", "#fbe45d", "#ff872a", "#f33351"])
ax.imshow(heat, extent=[0, 40, 20, 0], origin="upper", cmap=colors, alpha=np.clip(heat * 1.3, 0, .87), aspect="auto")
for p in r["positions"]:
    ax.scatter(p["x"], p["y"], c="#63aafa" if p["id"][0] == "A" else "#ff9f60", s=37, edgecolors="white", linewidths=.7)
    ax.text(p["x"], p["y"]-.55, p["id"], color="white", ha="center", fontsize=8)
ax.set_xlim(0, 40)
ax.set_ylim(20, 0)
ax.set_title("5v5 Futsal Player Position Heatmap (Educational Simulation)")
ax.set_xlabel("Field X (m)")
ax.set_ylabel("Field Y (m)")
fig.tight_layout()
fig.savefig("futsal_python_heatmap.png", dpi=160)
plt.show()

fig, ax = plt.subplots(figsize=(11, 4.7))
ax.plot(range(1, 13), r["traces"]["A"], color="#5298e9", marker="o", label="BLUE (A)")
ax.plot(range(1, 13), r["traces"]["B"], color="#ec965d", marker="s", label="ORANGE (B)")
ax.set_xlabel("Time interval (12 bins)")
ax.set_ylabel("Estimated travel distance (m)")
ax.set_title("Time-based Team Activity")
ax.grid(alpha=.25)
ax.legend()
fig.tight_layout()
fig.savefig("futsal_team_timeline.png", dpi=160)
plt.show()

# 추가 분석 결과 다운로드용 CSV
pd.DataFrame(r["players"]).to_csv("futsal_player_analysis.csv", index=False, encoding="utf-8-sig")
print("생성 파일: futsal_player_distance.png / futsal_python_heatmap.png / futsal_team_timeline.png / futsal_player_analysis.csv")
