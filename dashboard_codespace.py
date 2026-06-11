import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------- НАСТРОЙКА СТРАНИЦЫ -----------------------------
st.set_page_config(page_title="Футбольная аналитика АПЛ", layout="wide", page_icon="⚽")

# ----------------------------- ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ -----------------------------
# Создаем ОДНО соединение при запуске и используем его везде
@st.cache_resource
def get_connection():
    return sqlite3.connect('football_stats.db', check_same_thread=False)

# ----------------------------- ЗАГРУЗКА ДАННЫХ (ОДИН РАЗ) -----------------------------
@st.cache_data
def load_all_data():
    """Загружает все данные из БД"""
    conn = get_connection()
    
    # Загружаем игроков со статистикой
    players_query = """
        SELECT p.player_id, p.player_name, p.position, p.age, p.nationality, p.market_value_million,
               t.team_name, t.team_id,
               ps.goals, ps.assists, ps.matches, ps.minutes_played, 
               ps.xg, ps.xa, ps.passes_completed, ps.tackles
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        JOIN player_stats ps ON p.player_id = ps.player_id
        ORDER BY ps.goals DESC
    """
    players_df = pd.read_sql_query(players_query, conn)
    
    # Загружаем команды
    teams_df = pd.read_sql_query("SELECT team_id, team_name, city, stadium FROM teams ORDER BY team_name", conn)
    
    return players_df, teams_df

# Загружаем все данные
all_players_df, teams_df = load_all_data()

# Создаем вспомогательные словари
team_options = {row['team_name']: row['team_id'] for _, row in teams_df.iterrows()}
player_options = {row['player_name']: row['player_id'] for _, row in all_players_df.iterrows()}
player_names = list(player_options.keys())

# ----------------------------- БОКОВАЯ ПАНЕЛЬ (НАВИГАЦИЯ) -----------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/44/44930.png", width=50)
st.sidebar.title("⚽ Навигация")
page = st.sidebar.radio("Выберите раздел", [
    "📊 Главная", "🏆 Топ-листы", "📈 Аналитика", "🔍 Сравнение игроков", "📋 Все игроки"
])

# ========================= СТРАНИЦА 1: ГЛАВНАЯ =========================
if page == "📊 Главная":
    st.title("🏆 Футбольная аналитика АПЛ")
    st.markdown("### Анализ игроков английской Премьер-лиги | Сезон 2023/24")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⚽ Всего голов", int(all_players_df['goals'].sum()))
    with col2:
        st.metric("🎯 Всего передач", int(all_players_df['assists'].sum()))
    with col3:
        st.metric("🏃 Всего игроков", len(all_players_df))
    with col4:
        st.metric("💰 Суммарная стоимость", f"€{all_players_df['market_value_million'].sum():.0f}M")
    
    st.markdown("---")
    
    st.subheader("🔥 Топ-10 бомбардиров")
    top_scorers = all_players_df.nlargest(10, 'goals')
    fig = px.bar(top_scorers, x='goals', y='player_name', color='team_name',
                 orientation='h', title='Лучшие бомбардиры сезона',
                 text='goals', height=500)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# ========================= СТРАНИЦА 2: ТОП-ЛИСТЫ =========================
elif page == "🏆 Топ-листы":
    st.title("🏆 Рейтинги игроков")
    
    metric_names = {
        'goals': 'Голы',
        'assists': 'Голевые передачи',
        'xg': 'Ожидаемые голы (xG)',
        'xa': 'Ожидаемые передачи (xA)',
        'market_value_million': 'Рыночная стоимость (€M)',
        'passes_completed': 'Точные пасы',
        'tackles': 'Отборы'
    }
    
    col1, col2 = st.columns(2)
    with col1:
        metric = st.selectbox("Выберите метрику", list(metric_names.keys()), format_func=lambda x: metric_names[x])
        top_n = st.slider("Количество игроков в топе", 5, 20, 10)
        
        top_players = all_players_df.nlargest(top_n, metric)
        fig = px.bar(top_players, x=metric, y='player_name', color='team_name',
                     title=f"Топ-{top_n} по показателю: {metric_names[metric]}",
                     orientation='h', text=metric, height=500)
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Лучшие по версии G/A (гол + пас)")
        all_players_df['goal_assist'] = all_players_df['goals'] + all_players_df['assists']
        top_ga = all_players_df.nlargest(10, 'goal_assist')
        fig2 = px.bar(top_ga, x='goal_assist', y='player_name', color='team_name',
                      title="Goal + Assist (совокупный вклад)", orientation='h')
        st.plotly_chart(fig2, use_container_width=True)

# ========================= СТРАНИЦА 3: АНАЛИТИКА =========================
elif page == "📈 Аналитика":
    st.title("📈 Продвинутая аналитика")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Эффективность: Голы vs xG")
        fig1 = px.scatter(all_players_df, x='xg', y='goals', color='team_name',
                          size='market_value_million', hover_name='player_name',
                          text='player_name', title="Реальные голы vs Ожидаемые голы (xG)",
                          labels={'xg': 'xG (ожидаемые голы)', 'goals': 'Голы'})
        fig1.update_traces(textposition='top center')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("💰 Стоимость vs Результативность")
        fig2 = px.scatter(all_players_df, x='market_value_million', y='goals', color='team_name',
                          size='assists', hover_name='player_name',
                          title="Рыночная стоимость vs Забитые голы",
                          labels={'market_value_million': 'Рыночная стоимость (€M)', 'goals': 'Голы'})
        st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("🌀 Тепловая карта эффективности по позициям")
    position_stats = all_players_df.groupby('position').agg({
        'goals': 'mean', 'assists': 'mean', 'xg': 'mean', 'tackles': 'mean'
    }).reset_index()
    
    fig3 = px.imshow(position_stats.iloc[:, 1:].T, 
                     x=position_stats['position'], 
                     text_auto=True, 
                     title="Средние показатели по позициям",
                     labels=dict(x="Позиция", y="Метрика", color="Значение"),
                     color_continuous_scale='Blues')
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

# ========================= СТРАНИЦА 4: СРАВНЕНИЕ ИГРОКОВ =========================
elif page == "🔍 Сравнение игроков":
    st.title("🔍 Сравнение двух игроков")
    
    col1, col2 = st.columns(2)
    with col1:
        player1 = st.selectbox("Выберите первого игрока", player_names, index=0)
    with col2:
        player2 = st.selectbox("Выберите второго игрока", player_names, index=min(1, len(player_names)-1))
    
    if player1 and player2:
        p1 = all_players_df[all_players_df['player_name'] == player1].iloc[0]
        p2 = all_players_df[all_players_df['player_name'] == player2].iloc[0]
        
        compare_cols = ['goals', 'assists', 'xg', 'xa', 'matches', 'minutes_played', 'passes_completed', 'tackles']
        compare_names = {
            'goals': 'Голы', 'assists': 'Передачи', 'xg': 'xG', 'xa': 'xA',
            'matches': 'Матчи', 'minutes_played': 'Минуты', 
            'passes_completed': 'Пасы', 'tackles': 'Отборы'
        }
        
        st.subheader(f"📊 Сравнение: {player1} vs {player2}")
        
        # График сравнения
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name=player1,
            x=[compare_names[c] for c in compare_cols],
            y=[float(p1[c]) for c in compare_cols],
            marker_color='blue'
        ))
        fig.add_trace(go.Bar(
            name=player2,
            x=[compare_names[c] for c in compare_cols],
            y=[float(p2[c]) for c in compare_cols],
            marker_color='red'
        ))
        fig.update_layout(barmode='group', title=f"Сравнение статистики", height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Детальная информация
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### {player1}")
            st.write(f"**Команда:** {p1['team_name']}")
            st.write(f"**Позиция:** {p1['position']}")
            st.write(f"**Национальность:** {p1['nationality']}")
            st.write(f"**Возраст:** {p1['age']}")
            st.write(f"**Рыночная стоимость:** €{p1['market_value_million']}M")
        
        with c2:
            st.markdown(f"### {player2}")
            st.write(f"**Команда:** {p2['team_name']}")
            st.write(f"**Позиция:** {p2['position']}")
            st.write(f"**Национальность:** {p2['nationality']}")
            st.write(f"**Возраст:** {p2['age']}")
            st.write(f"**Рыночная стоимость:** €{p2['market_value_million']}M")

# ========================= СТРАНИЦА 5: ВСЕ ИГРОКИ =========================
else:
    st.title("📋 Полный список игроков")
    
    # Фильтры
    col1, col2 = st.columns(2)
    with col1:
        selected_team = st.selectbox("Фильтр по команде", ["Все"] + list(team_options.keys()))
    with col2:
        min_goals = st.number_input("Минимальное количество голов", min_value=0, max_value=30, value=0)
    
    # Применяем фильтры
    if selected_team != "Все":
        filtered_df = all_players_df[all_players_df['team_name'] == selected_team]
    else:
        filtered_df = all_players_df.copy()
    
    filtered_df = filtered_df[filtered_df['goals'] >= min_goals]
    
    st.dataframe(
        filtered_df[['player_name', 'team_name', 'position', 'age', 'nationality', 
                     'goals', 'assists', 'matches', 'market_value_million']],
        use_container_width=True
    )
    
    st.caption(f"Показано {len(filtered_df)} игроков из {len(all_players_df)}")