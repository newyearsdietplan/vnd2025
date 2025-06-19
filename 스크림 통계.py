import streamlit as st
import pandas as pd
st.set_page_config(page_title="발낳대 2025 - 스크림 통계", layout="wide")

# 데이터 로딩 및 컬럼 정리
df = pd.read_csv("data_scream.csv")
df.columns = df.columns.str.strip()

df.rename(columns={
    "닉네임": "스트리머 이름",
    "요원": "사용한 요원",
    "ACS": "전투 점수",
    "FK": "첫 킬",
    "FD": "첫 데스",
    "HS": "헤드샷%",
    "ADR": "피해량",
    "DDΔ": "피해량 격차",
    "MK": "멀티킬",
    "PL": "설치",
    "DF": "해체"
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
    "C": ["강지", "눈꽃", "마뫄", "빅헤드"],
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

# 팀 매핑 추가
team_map = {
    "강지형": "모운", "감제이": "츈츈", "강지": "모운", "아구이뽀": "모운", "고수달": "썬데",
    "김뚜띠": "썬데", "뱅": "모운", "눈꽃": "파인", "울프": "츈츈", "따효니": "모운",
    "조별하": "파인", "푸린": "파인", "마뫄": "츈츈", "유봄냥": "썬데", "러너": "츈츈",
    "짜누": "츈츈", "핑맨": "썬데", "빅헤드": "썬데", "임나은": "파인", "백곰파": "파인"
}
df["팀"] = df["스트리머 이름"].map(team_map).fillna("용병")

# 필터
team_options = sorted(df["팀"].unique())
selected_teams = st.sidebar.multiselect("팀 필터", team_options, default=[t for t in team_options if t != "용병"])
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
df = df[df["팀"].isin(selected_teams)]

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
    team = team_map.get(name, "?")
    return f"[{tier}-{team}] {name}" if tier != "용병" else f"[-] {name}"

def style_dataframe(df):
    return df.style.format({
        "승률": "{:.2f}",
        "전투 점수": "{:.2f}",
        "KD": "{:.2f}",
        "KDA": "{:.2f}",
        "KD": "{:.2f}",
        "KDA": "{:.2f}",
        "킬": "{:.1f}",
        "데스": "{:.1f}",
        "어시스트": "{:.1f}",
        "피해량": "{:.2f}",
        "피해량 격차": "{:.2f}",
        "헤드샷%": "{:.1f}",
        "첫 킬": "{:.1f}",
        "첫 데스": "{:.1f}",
        "멀티킬": "{:.1f}",
        "설치": "{:.1f}",
        "해체": "{:.1f}"
    })


# 통계 계산 함수
def compute_stats(g):
    # 멀티 인덱스 컬럼 평탄화
    g.columns = ['_'.join(col) if isinstance(col, tuple) else col for col in g.columns]

    # 컬럼 이름 정리
    g.rename(columns={
        "경기 번호_nunique": "경기 수",
        "킬_sum": "총 킬",
        "데스_sum": "총 데스",
        "어시스트_sum": "총 어시스트",
        "첫 킬_mean": "첫 킬",
        "첫 데스_mean": "첫 데스",
        "멀티킬_mean": "멀티킬",
        "설치_mean": "설치",
        "해체_mean": "해체",
        "전투 점수_mean": "전투 점수",
        "피해량_mean": "피해량",
        "피해량 격차_mean": "피해량 격차",
        "헤드샷%_mean": "헤드샷%",
        "KD_mean": "dummy_KD",
        "KDA_mean": "dummy_KDA",
        "승리_sum": "승리",
        "승리_mean": "승률"
    }, inplace=True)

    # 파생 통계
    g["KD"] = g["총 킬"] / g["총 데스"]
    g["KDA"] = (g["총 킬"] + g["총 어시스트"]) / g["총 데스"]
    g["킬"] = g["총 킬"] / g["경기 수"]
    g["데스"] = g["총 데스"] / g["경기 수"]
    g["어시스트"] = g["총 어시스트"] / g["경기 수"]

    # 출력 열 순서 정리
    g = g[[
        "경기 수", "승률", "KD", "KDA", "전투 점수", "첫 킬", "첫 데스",
        "피해량", "피해량 격차", "헤드샷%", "멀티킬", "설치", "해체",
        "킬", "데스", "어시스트",
    ]]
    return g


# 공통 집계 사전
agg_dict = {
    "경기 번호": "nunique",
    "킬": "sum",
    "데스": "sum",
    "어시스트": "sum",
    "첫 킬": "mean",
    "첫 데스": "mean",     # 추가
    "멀티킬": "mean",     # 추가
    "설치": "mean",     # 추가
    "해체": "mean",     # 추가
    "전투 점수": "mean",
    "피해량": "mean",
    "피해량 격차": "mean",
    "헤드샷%": "mean",
    "KD": "mean",
    "KDA": "mean",
    "승리": ["sum", "mean"]
}


def get_rounds_score(game_data, team1, team2):
    # 팀별 rounds 컬럼의 값들을 유니크하게 가져옴
    team1_rounds = game_data[game_data["팀"] == team1]["rounds"].dropna().unique()
    team2_rounds = game_data[game_data["팀"] == team2]["rounds"].dropna().unique()

    # 각 팀의 rounds 값이 여러개 있으면 가장 흔한 값을 선택하거나 첫 번째를 사용
    r1 = int(team1_rounds[0]) if len(team1_rounds) > 0 else 0
    r2 = int(team2_rounds[0]) if len(team2_rounds) > 0 else 0

    return r1, r2
    
# 메인 타이틀
st.title("🎮 발낳대 2025 스크림 통계")

# 메뉴 선택
menu = st.sidebar.radio("보기 항목을 선택하세요", (
    "8. 팀별 승률 및 상대전적",
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

    cols = ["경기 번호", "날짜", "스트리머 이름", "맵", "사용한 요원", "전투 점수", "KD", "KDA", "피해량", "피해량 격차", "헤드샷%", "첫 킬", "첫 데스", "멀티킬", "설치", "해체", "킬", "데스", "어시스트", "승패"]
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
    cols = ["경기 번호", "날짜", "스트리머 이름", "맵", "사용한 요원", "전투 점수", "KD", "KDA", "피해량", "피해량 격차", "헤드샷%", "첫 킬", "첫 데스", "멀티킬", "설치", "해체", "킬", "데스", "어시스트", "승패"]
    def highlight(row):
        color = "#d1f0d1" if row["승패"] == "v" else "#f8d0d0"
        return [f"background-color: {color}" for _ in row]
    st.dataframe(style_dataframe(subset[cols].sort_values(by=["날짜", "경기 번호"])).apply(highlight, axis=1), use_container_width=True, height=600)

if menu == "8. 팀별 승률 및 상대전적":
    st.header("팀별 승률 및 상대전적")

    if "경기 번호" in df.columns and "팀" in df.columns and "승패" in df.columns:
        # 경기별 팀별 선수 수 집계
        grouped = df.groupby(["경기 번호", "팀"]).size().reset_index(name="선수수")

        # 선수 3명 이상 팀만 필터링
        valid_teams_per_game = grouped[grouped["선수수"] >= 1]

        # 경기별, 팀별 승패 정보
        team_matches = df.groupby(["경기 번호", "팀"]).agg({"승패": "first"}).reset_index()

        # 선수 3명 이상 팀만 결합
        valid_team_matches = pd.merge(team_matches, valid_teams_per_game[["경기 번호", "팀"]], on=["경기 번호", "팀"])

        # 피벗 테이블 생성: 경기번호 x 팀 => 승패
        team_results = valid_team_matches.pivot(index="경기 번호", columns="팀", values="승패")

        teams = sorted(valid_team_matches["팀"].unique())

        # 팀별 승률 계산
        team_stats = []
        for team in teams:
            played = team_results[team].dropna()
            win = (played == "v").sum()
            loss = (played == "l").sum()
            total = win + loss
            winrate = win / total * 100 if total > 0 else 0
            team_stats.append({
                "팀명": team,
                "경기 수": total,
                "승": win,
                "패": loss,
                "승률": round(winrate, 2)
            })

        # 모운 vs 파인 2패 추가 (경기로 기록 안 된 것)
        extra_matches = [
            {"팀명": "모운", "경기 수": 2, "승": 0, "패": 2, "승률": 0.0},
            {"팀명": "파인", "경기 수": 2, "승": 2, "패": 0, "승률": 100.0},
        ]

        for extra in extra_matches:
            idx = next((i for i, d in enumerate(team_stats) if d["팀명"] == extra["팀명"]), None)
            if idx is not None:
                team_stats[idx]["경기 수"] += extra["경기 수"]
                team_stats[idx]["승"] += extra["승"]
                team_stats[idx]["패"] += extra["패"]
                team_stats[idx]["승률"] = round(team_stats[idx]["승"] / team_stats[idx]["경기 수"] * 100, 2)
            else:
                team_stats.append(extra)

        team_df = pd.DataFrame(team_stats).sort_values("승률", ascending=False)
        team_df["승률"] = team_df["승률"].map(lambda x: f"{x:.2f}%")

        # 팀별 상대전적 초기화
        result_matrix = pd.DataFrame(index=teams, columns=teams, data="")

        # 경기별 승패 기록 반영
        for game_id, game_data in team_results.iterrows():
            valid_teams = game_data.dropna().index.tolist()
            if len(valid_teams) == 2:
                t1, t2 = valid_teams
                r1, r2 = game_data[t1], game_data[t2]
                if r1 == "v":
                    current = result_matrix.loc[t1, t2]
                    if current == "":
                        current = "1승 0패"
                    else:
                        # 누적 승패 숫자 갱신
                        w, l = map(int, current.replace("승", "").replace("패", "").split())
                        current = f"{w+1}승 {l}패"
                    result_matrix.loc[t1, t2] = current

                    current_rev = result_matrix.loc[t2, t1]
                    if current_rev == "":
                        current_rev = "0승 1패"
                    else:
                        w, l = map(int, current_rev.replace("승", "").replace("패", "").split())
                        current_rev = f"{w}승 {l+1}패"
                    result_matrix.loc[t2, t1] = current_rev

                elif r2 == "v":
                    current = result_matrix.loc[t2, t1]
                    if current == "":
                        current = "1승 0패"
                    else:
                        w, l = map(int, current.replace("승", "").replace("패", "").split())
                        current = f"{w+1}승 {l}패"
                    result_matrix.loc[t2, t1] = current

                    current_rev = result_matrix.loc[t1, t2]
                    if current_rev == "":
                        current_rev = "0승 1패"
                    else:
                        w, l = map(int, current_rev.replace("승", "").replace("패", "").split())
                        current_rev = f"{w}승 {l+1}패"
                    result_matrix.loc[t1, t2] = current_rev

        # 모운팀 vs 파인팀 2패 추가
        if "파인" in result_matrix.index and "모운" in result_matrix.columns:
            for _ in range(2):
                current = result_matrix.loc["파인", "모운"]
                if current == "":
                    current = "1승 0패"
                else:
                    w, l = map(int, current.replace("승", "").replace("패", "").split())
                    current = f"{w+1}승 {l}패"
                result_matrix.loc["파인", "모운"] = current

                current_rev = result_matrix.loc["모운", "파인"] if "모운" in result_matrix.index and "파인" in result_matrix.columns else ""
                if current_rev == "":
                    current_rev = "0승 1패"
                else:
                    w, l = map(int, current_rev.replace("승", "").replace("패", "").split())
                    current_rev = f"{w}승 {l+1}패"
                result_matrix.loc["모운", "파인"] = current_rev

        # 대각선 칸 빈칸으로 처리
        for team in teams:
            result_matrix.loc[team, team] = "ㅡ"

        # 정렬 다시 맞추기
        result_matrix = result_matrix.loc[teams, teams]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 팀별 승률")
            st.dataframe(team_df.reset_index(drop=True), use_container_width=True, hide_index=True)
        with col2:
            st.subheader("⚔️ 팀별 상대 전적")
            st.dataframe(result_matrix, use_container_width=True)
            st.markdown("*모운팀과 파인팀의 첫 2경기는 승패만 기록됨*")

        st.markdown("---")
        st.subheader("📝 전적 상세")

        cols = ["경기 번호", "날짜", "스트리머 이름", "팀", "맵", "사용한 요원", "전투 점수", "KD", "KDA",
                "피해량", "피해량 격차", "헤드샷%", "첫 킬", "첫 데스", "멀티킬", "설치", "해체", "킬", "데스", "어시스트", "승패"]

        def highlight(row):
            color = "#d1f0d1" if row["승패"] == "v" else "#f8d0d0"
            return [f"background-color: {color}"] * len(row)

        recent_games = sorted(df["경기 번호"].unique(), reverse=True)[:10]
        for game_id in recent_games:
            game_data = df[df["경기 번호"] == game_id]

            # 선수 3명 이상 팀 필터링
            teams_in_game = game_data["팀"].value_counts()
            valid_teams = teams_in_game[teams_in_game >= 1].index.tolist()
            if len(valid_teams) != 2:
                continue

            team1, team2 = sorted(valid_teams)

            r1, r2 = get_rounds_score(game_data, team1, team2)

            st.markdown(f"### 경기 {game_id}: {team1} vs {team2} ({r1} : {r2})")

            subset = game_data[game_data["팀"].isin(valid_teams)].copy()
            subset = subset[cols]

            subset = subset.sort_values(by=["전투 점수"], ascending=False)

            subset_styled = subset.style.format({
                "전투 점수": "{:.2f}",
                "KD": "{:.2f}",
                "KDA": "{:.2f}"
            }).apply(highlight, axis=1)

            st.dataframe(subset_styled, use_container_width=True, height=400, hide_index=True)










