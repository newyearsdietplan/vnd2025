import streamlit as st
import pandas as pd
st.set_page_config(page_title="발낳대 2025 - 내전 통계", layout="wide")

# 데이터 로딩 및 컬럼 정리
df = pd.read_csv("pages/data.csv")
df.columns = df.columns.str.strip()  # 공백 제거

df.rename(columns={
    "닉네임": "스트리머 이름",
    "요원": "사용한 요원",
    "ACS": "전투 점수",
    "FK": "첫 킬",
    "HS": "헤드샷%",
    "ADR": "피해량",
    "DDΔ": "피해량 격차"
}, inplace=True)

# 승패 숫자 변환
if "승패" in df.columns:
    df["승리"] = df["승패"].map({"v": 1, "l": 0})
else:
    st.error("'승패' 컬럼이 누락되었습니다. data.csv 파일 구조를 확인하세요.")
    st.stop()

# 요원 역할 분류
agent_roles = {
    "타격대": ["네온", "레이나", "레이즈", "아이소", "요루", "웨이레이", "제트", "피닉스"],
    "척후대": ["게코", "브리치", "소바", "스카이", "케이/오", "테호", "페이드"],
    "감시자": ["데드록", "바이스", "사이퍼", "세이지", "체임버", "킬조이"],
    "전략가": ["바이퍼", "브림스톤", "아스트라", "오멘", "클로브", "하버"]
}

# 티어 분류
tiers = {
    "A": ["강지형", "김뚜띠", "조별하", "짜누"],
    "B": ["감제이", "뱅", "푸린", "핑맨"],
    "C": ["미친개정강지", "눈꽃", "마뫄", "빅헤드"],
    "D": ["아구이뽀", "울프", "유봄냥", "임나은"],
    "E": ["고수달", "따효니", "러너", "백곰파"]
}

# 용병 자동 추가
tiered = sum(tiers.values(), [])
all_streamers = df["스트리머 이름"].unique()
mercenaries = sorted(list(set(all_streamers) - set(tiered)))
if mercenaries:
    tiers["용병"] = mercenaries

streamer_tier_map = {s: tier for tier, lst in tiers.items() for s in lst}

# 필터
selected_tiers = st.sidebar.multiselect("티어 필터", list(tiers.keys()), default=[t for t in tiers.keys() if t != "용병"])
selected_tier_streamers = sum([tiers[tier] for tier in selected_tiers], [])
all_maps = sorted(df["맵"].unique())
selected_roles = st.sidebar.multiselect("요원 역할 필터", agent_roles.keys(), default=list(agent_roles.keys()))
selected_agents = sum([agent_roles[role] for role in selected_roles], [])
selected_maps = st.sidebar.multiselect("맵 필터", all_maps, default=all_maps)

# 필터 적용
df = df[df["스트리머 이름"].isin(selected_tier_streamers)]
df = df[df["사용한 요원"].isin(selected_agents)]
df = df[df["맵"].isin(selected_maps)]

# KDA, KD 계산
def compute_kda(row):
    return (row["킬"] + row["어시스트"]) / row["데스"] if row["데스"] != 0 else row["킬"] + row["어시스트"]

def compute_kd(row):
    return row["킬"] / row["데스"] if row["데스"] != 0 else row["킬"]

df["KDA"] = df.apply(compute_kda, axis=1)
df["KD"] = df.apply(compute_kd, axis=1)

# 정렬 기준
def tier_sort_key(name):
    order = ["A", "B", "C", "D", "E", "용병"]
    return (order.index(streamer_tier_map.get(name, "용병")), name)

def format_streamer_label(name):
    tier = streamer_tier_map.get(name, "-")
    return f"[-] {name}" if tier == "용병" else f"[{tier}] {name}"

def style_dataframe(df):
    return df.style.format({
        "승률": "{:.2f}",
        "전투 점수": "{:.2f}",
        "KD": "{:.2f}",
        "KDA": "{:.2f}",
        "평균 KD": "{:.2f}",
        "평균 KDA": "{:.2f}",
        "평균 킬": "{:.1f}",
        "평균 데스": "{:.1f}",
        "평균 어시스트": "{:.1f}",
        "피해량": "{:.2f}",
        "피해량 격차": "{:.2f}",
        "헤드샷%": "{:.1f}",
        "평균 첫 킬": "{:.1f}"
    })

# 통계 계산 함수
def compute_stats(g):
    g.columns = [
        "총 경기 수", "총 킬", "총 데스", "총 어시스트",
        "평균 첫 킬",
        "전투 점수", "피해량", "피해량 격차", "헤드샷%",
        "dummy_KD", "dummy_KDA", "총 승리 수", "승률"
    ]
    g["평균 KD"] = g["총 킬"] / g["총 데스"]
    g["평균 KDA"] = (g["총 킬"] + g["총 어시스트"]) / g["총 데스"]
    g["평균 킬"] = g["총 킬"] / g["총 경기 수"]
    g["평균 데스"] = g["총 데스"] / g["총 경기 수"]
    g["평균 어시스트"] = g["총 어시스트"] / g["총 경기 수"]
    g = g[[  # 순서 조정
        "총 경기 수", "승률", "평균 KD", "평균 KDA", "전투 점수", "평균 첫 킬",
        "피해량", "피해량 격차", "헤드샷%",
        "평균 킬", "평균 데스", "평균 어시스트"
    ]]
    return g

# 공통 집계 사전
agg_dict = {
    "경기 번호": "nunique",
    "킬": "sum",
    "데스": "sum",
    "어시스트": "sum",
    "첫 킬": "mean",
    "전투 점수": "mean",
    "피해량": "mean",
    "피해량 격차": "mean",
    "헤드샷%": "mean",
    "KD": "mean",
    "KDA": "mean",
    "승리": ["sum", "mean"]
}

# 메인 타이틀
st.title("🎮 발낳대 2025 내전 통계")

# 메뉴 선택
menu = st.sidebar.radio("보기 항목을 선택하세요", (
    "1. 스트리머별 종합 스탯",
    "2. 맵별 스트리머 스탯",
    "3. 스트리머의 요원별 스탯",
    "5. 스트리머의 맵별 스탯",
    "6. 스트리머의 맵-요원별 스탯",
    "4. 경기별 스트리머 스탯",
    "7. 스트리머의 모든 경기 확인"
))

if menu == "1. 스트리머별 종합 스탯":
    st.header("📊 스트리머별 종합 스탯")
    stats = df.groupby("스트리머 이름").agg(agg_dict)
    stats = compute_stats(stats)
    stats.index = [format_streamer_label(n) for n in stats.index]
    stats = stats.sort_values("전투 점수", ascending=False)
    st.dataframe(style_dataframe(stats), use_container_width=True, height=800)

elif menu == "2. 맵별 스트리머 스탯":
    st.header("🗺️ 맵별 스트리머 스탯")
    selected_map = st.selectbox("맵을 선택하세요", sorted(df["맵"].unique()))
    filtered = df[df["맵"] == selected_map]
    stats = filtered.groupby("스트리머 이름").agg(agg_dict)
    stats = compute_stats(stats)
    stats.index = [format_streamer_label(n) for n in stats.index]
    stats = stats.sort_values("전투 점수", ascending=False)
    st.dataframe(style_dataframe(stats), use_container_width=True, height=800)

elif menu == "3. 스트리머의 요원별 스탯":
    st.header("🧍‍♀️ 스트리머의 요원별 스탯")
    streamer_options = sorted(df["스트리머 이름"].unique(), key=tier_sort_key)
    selected = st.selectbox("스트리머를 선택하세요", streamer_options)
    subset = df[df["스트리머 이름"] == selected]
    stats = subset.groupby("사용한 요원").agg(agg_dict)
    stats = compute_stats(stats)
    stats = stats.sort_values("전투 점수", ascending=False)
    st.dataframe(style_dataframe(stats), use_container_width=True, height=800)

elif menu == "4. 경기별 스트리머 스탯":
    st.header("📅 경기별 스트리머 스탯")

    game_info_options = []
    for game_id in sorted(df["경기 번호"].unique()):
        game_df = df[df["경기 번호"] == game_id]
        if not game_df.empty:
            date = game_df["날짜"].iloc[0]
            map_name = game_df["맵"].iloc[0]
            players = ', '.join(sorted(game_df["스트리머 이름"].unique()))
            label = f"{game_id}, {date}, {map_name}, {players}"
            game_info_options.append((label, game_id))

    selected_label = st.selectbox("경기 번호를 선택하세요", [label for label, _ in game_info_options])
    selected_game = dict(game_info_options)[selected_label]

    subset = df[df["경기 번호"] == selected_game].copy()

    def highlight(row):
        color = "#d1f0d1" if row["승패"] == "v" else "#f8d0d0"
        return [f"background-color: {color}" for _ in row]

    subset["KDA"] = subset.apply(compute_kda, axis=1)
    subset["KD"] = subset.apply(compute_kd, axis=1)

    cols = ["경기 번호", "날짜", "스트리머 이름", "맵", "사용한 요원", "전투 점수", "KD", "KDA", "피해량", "피해량 격차", "헤드샷%", "첫 킬", "킬", "데스", "어시스트", "승패"]
    st.dataframe(style_dataframe(subset[cols]).apply(highlight, axis=1), use_container_width=True, height=600)


elif menu == "5. 스트리머의 맵별 스탯":
    st.header("🧭 스트리머의 맵별 스탯")
    streamer_options = sorted(df["스트리머 이름"].unique(), key=tier_sort_key)
    selected = st.selectbox("스트리머를 선택하세요", streamer_options)
    subset = df[df["스트리머 이름"] == selected]
    stats = subset.groupby("맵").agg(agg_dict)
    stats = compute_stats(stats)
    stats = stats.sort_values("전투 점수", ascending=False)
    st.dataframe(style_dataframe(stats), use_container_width=True, height=800)

elif menu == "6. 스트리머의 맵-요원별 스탯":
    st.header("🧩 스트리머의 맵-요원별 스탯")
    streamer_options = sorted(df["스트리머 이름"].unique(), key=tier_sort_key)
    selected = st.selectbox("스트리머를 선택하세요", streamer_options)
    subset = df[df["스트리머 이름"] == selected]
    map_options = sorted(subset["맵"].unique())
    selected_map = st.selectbox("맵을 선택하세요", map_options)
    filtered = subset[subset["맵"] == selected_map]
    stats = filtered.groupby("사용한 요원").agg(agg_dict)
    stats = compute_stats(stats)
    stats = stats.sort_values("전투 점수", ascending=False)
    st.dataframe(style_dataframe(stats), use_container_width=True, height=800)

elif menu == "7. 스트리머의 모든 경기 확인":
    st.header("🧾 스트리머의 모든 경기 기록")
    streamer_options = sorted(df["스트리머 이름"].unique(), key=tier_sort_key)
    selected = st.selectbox("스트리머를 선택하세요", streamer_options)
    subset = df[df["스트리머 이름"] == selected].copy()
    subset["KDA"] = subset.apply(compute_kda, axis=1)
    subset["KD"] = subset.apply(compute_kd, axis=1)
    cols = ["경기 번호", "날짜", "스트리머 이름", "맵", "사용한 요원", "전투 점수", "KD", "KDA", "피해량", "피해량 격차", "헤드샷%", "첫 킬", "킬", "데스", "어시스트", "승패"]
    def highlight(row):
        color = "#d1f0d1" if row["승패"] == "v" else "#f8d0d0"
        return [f"background-color: {color}" for _ in row]
    st.dataframe(style_dataframe(subset[cols].sort_values(by=["날짜", "경기 번호"])).apply(highlight, axis=1), use_container_width=True, height=600)
