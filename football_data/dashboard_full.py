import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3

st.set_page_config(page_title="Футбольная аналитика АПЛ", layout="wide", page_icon="⚽")

@st.cache_resource
def get_connection():
    return sqlite3.connect('football_stats_ready.db', check_same_thread=False)

@st.cache_data
def load_all_data():
    conn = get_connection()
    players_df = pd.read_sql_query("SELECT * FROM players", conn)
    teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
    numeric_cols = ['goals', 'assists', 'minutes', 'now_cost', 'form', 'expected_goals', 'expected_assists']
    for col in numeric_cols:
        if col in players_df.columns:
            players_df[col] = pd.to_numeric(players_df[col], errors='coerce').fillna(0)
    return players_df, teams_df

players_df, teams_df = load_all_data()
teams_list = sorted(players_df['team_name'].unique())
positions_list = sorted(players_df['position'].unique())

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/44/44930.png", width=50)
st.sidebar.title("⚽ Навигация")
page = st.sidebar.radio("Выберите раздел", ["📊 Главная", "🏆 Топ-листы", "🔍 Сравнение игроков", "🎯 Прогноз матча", "📋 Все игроки"])

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Фильтры")
selected_team = st.sidebar.selectbox("Команда", ["Все"] + teams_list)
selected_position = st.sidebar.selectbox("Позиция", ["Все"] + positions_list)
min_goals = st.sidebar.slider("Минимум голов", 0, 30, 0)

filtered_df = players_df.copy()
if selected_team != "Все":
    filtered_df = filtered_df[filtered_df['team_name'] == selected_team]
if selected_position != "Все":
    filtered_df = filtered_df[filtered_df['position'] == selected_position]
filtered_df = filtered_df[filtered_df['goals'] >= min_goals]

if page == "📊 Главная":
    st.title("⚽ Футбольная аналитика АПЛ")
    st.markdown("**Сезон 2025/26 | Данные: FPL Stats**")
    if len(filtered_df) > 0:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏃 Игроков", len(filtered_df))
        with col2:
            st.metric("⚽ Голов", int(filtered_df['goals'].sum()))
        with col3:
            st.metric("🎯 Передач", int(filtered_df['assists'].sum()))
        with col4:
            avg_minutes = filtered_df['minutes'].mean()
            st.metric("⏱️ Средние минуты", int(avg_minutes) if not pd.isna(avg_minutes) else 0)
        st.markdown("---")
        st.subheader("🏆 Топ-10 бомбардиров")
        top_scorers = filtered_df.nlargest(10, 'goals')
        if len(top_scorers) > 0 and top_scorers['goals'].sum() > 0:
            fig = px.bar(top_scorers, x='goals', y='web_name', color='team_name', orientation='h', text='goals', height=500)
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных о голах для выбранных фильтров")
    else:
        st.warning("Нет данных, соответствующих выбранным фильтрам")

elif page == "🏆 Топ-листы":
    st.title("🏆 Рейтинги игроков")
    if len(filtered_df) > 0:
        metric_options = {'goals': 'Голы', 'assists': 'Передачи', 'expected_goals': 'xG', 'minutes': 'Минуты', 'form': 'Форма', 'now_cost': 'Стоимость'}
        col1, col2 = st.columns(2)
        with col1:
            selected_metric = st.selectbox("Метрика", list(metric_options.keys()), format_func=lambda x: metric_options[x])
        with col2:
            top_n = st.slider("Количество", 5, 30, 10)
        sorted_df = filtered_df.nlargest(top_n, selected_metric)
        if len(sorted_df) > 0 and sorted_df[selected_metric].sum() > 0:
            fig = px.bar(sorted_df, x=selected_metric, y='web_name', color='team_name', orientation='h')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Нет данных по метрике '{metric_options[selected_metric]}'")
    else:
        st.warning("Нет данных для выбранных фильтров")

elif page == "🔍 Сравнение игроков":
    st.title("🔍 Сравнение игроков")
    if len(filtered_df) >= 2:
        player_names = filtered_df['web_name'].tolist()
        col1, col2 = st.columns(2)
        with col1:
            player1 = st.selectbox("Игрок 1", player_names, index=0)
        with col2:
            player2 = st.selectbox("Игрок 2", player_names, index=min(1, len(player_names)-1))
        if player1 and player2:
            p1 = filtered_df[filtered_df['web_name'] == player1].iloc[0]
            p2 = filtered_df[filtered_df['web_name'] == player2].iloc[0]
            compare_cols = ['goals', 'assists', 'minutes', 'form', 'now_cost']
            compare_names = ['Голы', 'Передачи', 'Минуты', 'Форма', 'Стоимость']
            fig = go.Figure()
            fig.add_trace(go.Bar(name=player1, x=compare_names, y=[p1[c] for c in compare_cols], marker_color='blue'))
            fig.add_trace(go.Bar(name=player2, x=compare_names, y=[p2[c] for c in compare_cols], marker_color='red'))
            fig.update_layout(barmode='group', height=500)
            st.plotly_chart(fig, use_container_width=True)
    elif len(filtered_df) == 1:
        st.warning("Выбран только 1 игрок. Добавьте ещё игроков, изменив фильтры.")
    else:
        st.warning("Нет игроков для выбранных фильтров")

elif page == "🎯 Прогноз матча":
    st.title("🎯 Прогноз матча")
    if len(teams_df) > 0:
        col1, col2 = st.columns(2)
        with col1:
            home_team = st.selectbox("Хозяева", teams_df['name'].tolist())
        with col2:
            away_team = st.selectbox("Гости", teams_df['name'].tolist())
        if st.button("Прогноз"):
            home = teams_df[teams_df['name'] == home_team].iloc[0]
            away = teams_df[teams_df['name'] == away_team].iloc[0]
            home_attack = (home['strength_attack_home'] + home['strength_attack_away']) / 2
            away_defence = (away['strength_defence_home'] + away['strength_defence_away']) / 2
            home_goals = (home_attack / max(away_defence, 1)) * 1.2
            away_goals = ((away['strength_attack_home'] + away['strength_attack_away']) / 2 / max(home['strength_defence_home'] + home['strength_defence_away'], 1)) * 0.8
            st.metric(f"🏠 {home_team}", f"{home_goals:.1f} гола")
            st.metric(f"✈️ {away_team}", f"{away_goals:.1f} гола")
            if home_goals > away_goals:
                st.success(f"Фаворит: {home_team}")
            elif away_goals > home_goals:
                st.success(f"Фаворит: {away_team}")
            else:
                st.info("Ожидается равный матч")
    else:
        st.warning("Нет данных о командах")

else:
    st.title("📋 Все игроки")
    if len(filtered_df) > 0:
        search_term = st.text_input("Поиск игрока")
        if search_term:
            filtered_df = filtered_df[filtered_df['web_name'].str.contains(search_term, case=False)]
        st.dataframe(filtered_df[['web_name', 'team_name', 'position', 'goals', 'assists', 'minutes']], use_container_width=True)
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("Скачать CSV", csv, "players.csv", "text/csv")
        st.caption(f"Показано {len(filtered_df)} игроков")
    else:
        st.warning("Нет данных для выбранных фильтров")