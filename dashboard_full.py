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
    return sqlite3.connect('football_stats_ready.db', check_same_thread=False)

@st.cache_data
def load_players():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM players", conn)
    # Конвертируем числовые колонки
    numeric_cols = ['goals', 'assists', 'minutes', 'now_cost', 'form', 'expected_goals', 'expected_assists']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    conn.close()
    return df

@st.cache_data
def load_teams():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM teams", conn)
    conn.close()
    return df

# Загрузка данных
players_df = load_players()
teams_df = load_teams()

# Словари для фильтров
teams_list = sorted(players_df['team_name'].unique())
positions_list = sorted(players_df['position'].unique())

# ==================== БОКОВАЯ ПАНЕЛЬ ====================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/44/44930.png", width=50)
st.sidebar.title("⚽ Навигация")

page = st.sidebar.radio("Выберите раздел", [
    "📊 Главная", 
    "🏆 Топ-листы", 
    "🔍 Сравнение игроков", 
    "🎯 Прогноз матча",
    "📋 Все игроки"
])

# Фильтры для всех страниц (кроме прогноза)
st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Фильтры")

# Фильтр по команде
selected_team = st.sidebar.selectbox("Команда", ["Все"] + teams_list)

# Фильтр по позиции
selected_position = st.sidebar.selectbox("Позиция", ["Все"] + positions_list)

# Фильтр по минимальному количеству голов
min_goals = st.sidebar.slider("Минимум голов", 0, 30, 0)

# Применяем фильтры
filtered_df = players_df.copy()
if selected_team != "Все":
    filtered_df = filtered_df[filtered_df['team_name'] == selected_team]
if selected_position != "Все":
    filtered_df = filtered_df[filtered_df['position'] == selected_position]
filtered_df = filtered_df[filtered_df['goals'] >= min_goals]

# ==================== СТРАНИЦА 1: ГЛАВНАЯ ====================
if page == "📊 Главная":
    st.title("⚽ Футбольная аналитика АПЛ")
    st.markdown("**Сезон 2025/26 | Данные: FPL Stats**")
    
    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏃 Игроков", len(filtered_df))
    with col2:
        st.metric("⚽ Голов", int(filtered_df['goals'].sum()))
    with col3:
        st.metric("🎯 Передач", int(filtered_df['assists'].sum()))
    with col4:
        st.metric("⏱️ Средние минуты", int(filtered_df['minutes'].mean()))
    
    st.markdown("---")
    
    # Топ-10 бомбардиров
    st.subheader("🏆 Топ-10 бомбардиров")
    top_scorers = filtered_df.nlargest(10, 'goals')
    if len(top_scorers) > 0:
        fig = px.bar(top_scorers, x='goals', y='web_name', color='team_name',
                     orientation='h', title='Лучшие бомбардиры', text='goals',
                     height=500)
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Нет данных")
    
    # График: Голы vs xG
    st.subheader("📈 Эффективность: Голы vs xG")
    if 'expected_goals' in filtered_df.columns:
        filtered_for_chart = filtered_df[filtered_df['minutes'] > 500]
        if len(filtered_for_chart) > 5:
            fig2 = px.scatter(filtered_for_chart, x='expected_goals', y='goals',
                              color='team_name', size='minutes',
                              hover_name='web_name', text='web_name',
                              title="Реальные голы vs Ожидаемые (xG)")
            fig2.update_traces(textposition='top center')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Недостаточно данных для графика")

# ==================== СТРАНИЦА 2: ТОП-ЛИСТЫ ====================
elif page == "🏆 Топ-листы":
    st.title("🏆 Рейтинги игроков")
    
    metric_options = {
        'goals': 'Голы',
        'assists': 'Голевые передачи',
        'expected_goals': 'Ожидаемые голы (xG)',
        'expected_assists': 'Ожидаемые передачи (xA)',
        'minutes': 'Минуты на поле',
        'form': 'Форма',
        'now_cost': 'Стоимость (£M)'
    }
    
    col1, col2 = st.columns(2)
    with col1:
        selected_metric = st.selectbox("Выберите метрику", list(metric_options.keys()), format_func=lambda x: metric_options[x])
    with col2:
        top_n = st.slider("Количество игроков", 5, 30, 10)
    
    # Сортировка и отображение
    sorted_df = filtered_df.nlargest(top_n, selected_metric)
    fig = px.bar(sorted_df, x=selected_metric, y='web_name', color='team_name',
                 title=f"Топ-{top_n} по {metric_options[selected_metric]}",
                 orientation='h', text=selected_metric)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# ==================== СТРАНИЦА 3: СРАВНЕНИЕ ИГРОКОВ ====================
elif page == "🔍 Сравнение игроков":
    st.title("🔍 Сравнение двух игроков")
    
    player_names = filtered_df['web_name'].tolist()
    
    col1, col2 = st.columns(2)
    with col1:
        player1 = st.selectbox("Игрок 1", player_names, index=0 if len(player_names) > 0 else None)
    with col2:
        player2 = st.selectbox("Игрок 2", player_names, index=min(1, len(player_names)-1) if len(player_names) > 1 else None)
    
    if player1 and player2:
        p1 = filtered_df[filtered_df['web_name'] == player1].iloc[0]
        p2 = filtered_df[filtered_df['web_name'] == player2].iloc[0]
        
        compare_cols = ['goals', 'assists', 'expected_goals', 'expected_assists', 'minutes', 'form', 'now_cost']
        compare_names = ['Голы', 'Передачи', 'xG', 'xA', 'Минуты', 'Форма', 'Стоимость']
        
        # Таблица сравнения
        compare_df = pd.DataFrame({
            'Показатель': compare_names,
            player1: [p1[c] for c in compare_cols],
            player2: [p2[c] for c in compare_cols]
        })
        st.dataframe(compare_df, use_container_width=True)
        
        # График сравнения
        fig = go.Figure()
        fig.add_trace(go.Bar(name=player1, x=compare_names, y=[p1[c] for c in compare_cols], marker_color='blue'))
        fig.add_trace(go.Bar(name=player2, x=compare_names, y=[p2[c] for c in compare_cols], marker_color='red'))
        fig.update_layout(barmode='group', title=f"{player1} vs {player2}", height=500)
        st.plotly_chart(fig, use_container_width=True)

# ==================== СТРАНИЦА 4: ПРОГНОЗ МАТЧА ====================
elif page == "🎯 Прогноз матча":
    st.title("🎯 Прогноз матча")
    st.markdown("На основе силы атаки и защиты команд (данные из teams.csv)")
    
    if len(teams_df) > 0:
        col1, col2 = st.columns(2)
        with col1:
            home_team = st.selectbox("🏠 Хозяева", teams_df['name'].tolist())
        with col2:
            away_team = st.selectbox("✈️ Гости", teams_df['name'].tolist())
        
        if st.button("Сделать прогноз", type="primary"):
            home = teams_df[teams_df['name'] == home_team].iloc[0]
            away = teams_df[teams_df['name'] == away_team].iloc[0]
            
            # Расчет ожидаемых голов
            home_attack = (home['strength_attack_home'] + home['strength_attack_away']) / 2
            away_defence = (away['strength_defence_home'] + away['strength_defence_away']) / 2
            away_attack = (away['strength_attack_home'] + away['strength_attack_away']) / 2
            home_defence = (home['strength_defence_home'] + home['strength_defence_away']) / 2
            
            expected_home = (home_attack / max(away_defence, 1)) * 1.2
            expected_away = (away_attack / max(home_defence, 1)) * 0.8
            
            expected_home = min(max(expected_home, 0.3), 3.5)
            expected_away = min(max(expected_away, 0.2), 3.0)
            
            # Вероятности
            total_goals = expected_home + expected_away
            home_win_prob = expected_home / total_goals * 0.7 if total_goals > 0 else 0.35
            away_win_prob = expected_away / total_goals * 0.7 if total_goals > 0 else 0.35
            draw_prob = 1 - home_win_prob - away_win_prob
            
            st.markdown("---")
            st.subheader(f"📊 Прогноз: {home_team} vs {away_team}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"🏠 {home_team}", f"{expected_home:.1f} гола", delta=f"{home_win_prob*100:.0f}% победа")
            with col2:
                st.metric("🤝 Ничья", f"{draw_prob*100:.0f}%")
            with col3:
                st.metric(f"✈️ {away_team}", f"{expected_away:.1f} гола", delta=f"{away_win_prob*100:.0f}% победа")
            
            # График вероятностей
            fig = go.Figure(data=[
                go.Bar(name='Вероятность', x=[home_team, 'Ничья', away_team],
                       y=[home_win_prob*100, draw_prob*100, away_win_prob*100],
                       marker_color=['blue', 'gray', 'red'])
            ])
            fig.update_layout(title="Вероятность исходов (%)", yaxis_title="%")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Нет данных о командах для прогноза")

# ==================== СТРАНИЦА 5: ВСЕ ИГРОКИ ====================
else:
    st.title("📋 Все игроки")
    
    # Поиск по имени
    search_term = st.text_input("🔍 Поиск игрока по имени", "")
    if search_term:
        filtered_df = filtered_df[filtered_df['web_name'].str.contains(search_term, case=False)]
    
    # Отображение таблицы
    display_cols = ['web_name', 'team_name', 'position', 'goals', 'assists', 'expected_goals', 'minutes', 'now_cost', 'form']
    existing_cols = [col for col in display_cols if col in filtered_df.columns]
    
    st.dataframe(filtered_df[existing_cols], use_container_width=True)
    
    # Кнопка экспорта
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Скачать данные в CSV", csv, "players_data.csv", "text/csv")
    
    st.caption(f"Показано {len(filtered_df)} игроков")