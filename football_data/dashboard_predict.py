import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import numpy as np

st.set_page_config(page_title="Футбольная аналитика АПЛ", layout="wide", page_icon="⚽")

# Подключение к БД
@st.cache_resource
def get_connection():
    return sqlite3.connect('football_stats.db', check_same_thread=False)

@st.cache_data
def load_teams():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM teams ORDER BY name", conn)
    return df

@st.cache_data
def load_players(min_minutes=100):
    conn = get_connection()
    df = pd.read_sql_query(f"""
        SELECT player_code, web_name, team_name, position, 
               goals, assists, expected_goals, expected_assists,
               minutes, form, points_per_game, influence, creativity, threat, now_cost
        FROM players 
        WHERE minutes >= {min_minutes}
        ORDER BY goals DESC
    """, conn)
    
    # Конвертируем числовые колонки
    numeric_cols = ['goals', 'assists', 'expected_goals', 'expected_assists', 
                    'minutes', 'form', 'points_per_game', 'influence', 'creativity', 
                    'threat', 'now_cost']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# Загружаем данные
teams_df = load_teams()
players_df = load_players(min_minutes=0)  # Загружаем всех, потом отфильтруем

# Фильтруем игроков с минутами
players_filtered = players_df[players_df['minutes'] >= 100].copy()

st.title("⚽ Футбольная аналитика АПЛ")
st.markdown("**Сезон 2025/26 | Данные: FPL Stats**")

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/44/44930.png", width=50)
st.sidebar.title("Навигация")
page = st.sidebar.radio("Выберите раздел", [
    "🏆 Главная", "📊 Топ-листы", "🎯 Прогноз матча", "🔍 Сравнение игроков", "📋 Все игроки"
])

# --- ФУНКЦИЯ ПРОГНОЗА МАТЧА ---
def predict_match(home_team, away_team, teams_df):
    """Прогнозирует исход матча на основе силы команд"""
    home = teams_df[teams_df['name'] == home_team].iloc[0]
    away = teams_df[teams_df['name'] == away_team].iloc[0]
    
    # Расчет ожидаемых голов
    home_attack = (home['strength_attack_home'] + home['strength_attack_away']) / 2
    away_defence = (away['strength_defence_home'] + away['strength_defence_away']) / 2
    away_attack = (away['strength_attack_home'] + away['strength_attack_away']) / 2
    home_defence = (home['strength_defence_home'] + home['strength_defence_away']) / 2
    
    expected_home_goals = (home_attack / max(away_defence, 0.5)) * 1.2
    expected_away_goals = (away_attack / max(home_defence, 0.5)) * 0.8
    
    expected_home_goals = min(max(expected_home_goals, 0.3), 3.5)
    expected_away_goals = min(max(expected_away_goals, 0.2), 3.0)
    
    # Вероятности исходов
    diff = expected_home_goals - expected_away_goals
    home_win_prob = 1 / (1 + np.exp(-diff * 1.5))
    away_win_prob = 1 / (1 + np.exp(diff * 1.5))
    draw_prob = 1 - home_win_prob - away_win_prob
    
    return {
        'home_goals': round(expected_home_goals, 1),
        'away_goals': round(expected_away_goals, 1),
        'home_win': round(home_win_prob * 100, 1),
        'draw': round(draw_prob * 100, 1),
        'away_win': round(away_win_prob * 100, 1)
    }

# ======================= СТРАНИЦЫ =======================

# --- ГЛАВНАЯ ---
if page == "🏆 Главная":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏃 Игроков (100+ мин)", len(players_filtered))
    with col2:
        st.metric("⚽ Всего голов", int(players_filtered['goals'].sum()))
    with col3:
        st.metric("🎯 Всего передач", int(players_filtered['assists'].sum()))
    with col4:
        st.metric("💰 Средняя стоимость", f"£{players_filtered['now_cost'].mean():.1f}M")
    
    st.subheader("🔥 Топ-10 бомбардиров")
    top_scorers = players_filtered.nlargest(10, 'goals')
    if len(top_scorers) > 0:
        fig = px.bar(top_scorers, x='goals', y='web_name', color='team_name',
                     orientation='h', title='Лучшие бомбардиры сезона',
                     text='goals', height=500)
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Нет данных для отображения")
    
    st.subheader("🎯 xG vs Goals (эффективность)")
    filtered = players_filtered[players_filtered['minutes'] > 300]
    if len(filtered) > 5:
        fig2 = px.scatter(filtered, x='expected_goals', y='goals', color='team_name',
                          size='minutes', hover_name='web_name',
                          title="Реальные голы vs Ожидаемые (xG)",
                          labels={'expected_goals': 'xG (ожидаемые голы)', 'goals': 'Голы'})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Недостаточно данных для отображения графика")

# --- ТОП-ЛИСТЫ ---
elif page == "📊 Топ-листы":
    st.title("📊 Рейтинги игроков")
    
    metric_names = {
        'goals': 'Голы', 'assists': 'Передачи', 'expected_goals': 'xG',
        'expected_assists': 'xA', 'influence': 'Влияние', 'creativity': 'Креативность',
        'threat': 'Угроза', 'form': 'Форма', 'points_per_game': 'Очки за матч',
        'now_cost': 'Стоимость (£M)'
    }
    
    metric = st.selectbox("Выберите метрику", list(metric_names.keys()), format_func=lambda x: metric_names[x])
    top_n = st.slider("Количество игроков", 5, 30, 10)
    
    top_players = players_filtered.nlargest(top_n, metric)
    if len(top_players) > 0:
        fig = px.bar(top_players, x=metric, y='web_name', color='team_name',
                     title=f"Топ-{top_n} по {metric_names[metric]}", orientation='h')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Нет данных для отображения")

# --- ПРОГНОЗ МАТЧА ---
elif page == "🎯 Прогноз матча":
    st.title("🎯 Прогноз матча")
    st.markdown("На основе силы атаки и защиты команд (ELO-модель)")
    
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("🏠 Хозяева", teams_df['name'].tolist())
    with col2:
        away_team = st.selectbox("✈️ Гости", teams_df['name'].tolist())
    
    if st.button("Сделать прогноз", type="primary"):
        prediction = predict_match(home_team, away_team, teams_df)
        
        st.markdown("---")
        st.subheader(f"📊 Прогноз: {home_team} vs {away_team}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"🏠 {home_team}", f"{prediction['home_goals']} гола", delta=f"{prediction['home_win']}% победа")
        with col2:
            st.metric("🤝 Ничья", f"{prediction['draw']}%")
        with col3:
            st.metric(f"✈️ {away_team}", f"{prediction['away_goals']} гола", delta=f"{prediction['away_win']}% победа")
        
        fig = go.Figure(data=[
            go.Bar(name='Вероятность', x=[home_team, 'Ничья', away_team],
                   y=[prediction['home_win'], prediction['draw'], prediction['away_win']],
                   marker_color=['blue', 'gray', 'red'])
        ])
        fig.update_layout(title="Вероятность исходов", yaxis_title="%")
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("ℹ️ Модель учитывает силу атаки/защиты команд и преимущество домашнего поля.")

# --- СРАВНЕНИЕ ИГРОКОВ ---
elif page == "🔍 Сравнение игроков":
    st.title("🔍 Сравнение двух игроков")
    
    player_names = players_filtered['web_name'].tolist()
    if len(player_names) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            player1 = st.selectbox("Игрок 1", player_names, index=0)
        with col2:
            player2 = st.selectbox("Игрок 2", player_names, index=min(1, len(player_names)-1))
        
        if player1 and player2:
            p1 = players_filtered[players_filtered['web_name'] == player1].iloc[0]
            p2 = players_filtered[players_filtered['web_name'] == player2].iloc[0]
            
            compare_cols = ['goals', 'assists', 'expected_goals', 'expected_assists', 
                            'influence', 'creativity', 'threat', 'form', 'points_per_game']
            compare_names = ['Голы', 'Передачи', 'xG', 'xA', 'Влияние', 'Креативность', 'Угроза', 'Форма', 'Очки/матч']
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name=player1, x=compare_names, y=[p1[c] for c in compare_cols], marker_color='blue'))
            fig.add_trace(go.Bar(name=player2, x=compare_names, y=[p2[c] for c in compare_cols], marker_color='red'))
            fig.update_layout(barmode='group', title=f"{player1} vs {player2}", height=500)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Недостаточно игроков для сравнения")

# --- ВСЕ ИГРОКИ ---
else:
    st.title("📋 Все игроки")
    
    filter_team = st.selectbox("Фильтр по команде", ["Все"] + sorted(players_filtered['team_name'].unique().tolist()))
    
    if filter_team != "Все":
        filtered = players_filtered[players_filtered['team_name'] == filter_team]
    else:
        filtered = players_filtered
    
    filtered = filtered.sort_values('goals', ascending=False)
    
    st.dataframe(filtered[['web_name', 'team_name', 'position', 'goals', 'assists', 
                           'expected_goals', 'form', 'minutes', 'now_cost']], 
                 use_container_width=True)
    st.caption(f"Показано {len(filtered)} игроков из {len(players_filtered)}")