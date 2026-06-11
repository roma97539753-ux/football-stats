import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

# ⚠️ ЗАМЕНИТЕ НА ВАШУ ССЫЛКУ ИЗ SUPABASE
DATABASE_URL = "postgresql://postgres.venyuobqorgjakbbyxax:Romafedorov2100@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)

def load_players_list():
    engine = get_engine()
    query = "SELECT player_id, player_name, team_name FROM players JOIN teams ON players.team_id = teams.team_id ORDER BY player_name"
    df = pd.read_sql(query, engine)
    return df

def load_player_stats(player_id):
    engine = get_engine()
    query = text("""
        SELECT p.player_name, t.team_name, p.position, p.age,
               ps.goals, ps.assists, ps.matches, ps.xg, ps.xa
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        JOIN player_stats ps ON p.player_id = ps.player_id
        WHERE p.player_id = :pid
    """)
    df = pd.read_sql(query, engine, params={"pid": player_id})
    return df.iloc[0] if not df.empty else None

def load_all_stats():
    engine = get_engine()
    query = """
        SELECT p.player_name, t.team_name, p.position, p.age,
               ps.goals, ps.assists, ps.matches, ps.xg, ps.xa
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        JOIN player_stats ps ON p.player_id = ps.player_id
        ORDER BY ps.goals DESC
    """
    return pd.read_sql(query, engine)

# --- Интерфейс Streamlit ---
st.set_page_config(page_title="Футбольная аналитика", layout="wide")
st.title("⚽ Анализ футбольной статистики АПЛ")
st.markdown("**База данных: PostgreSQL (Supabase) | Сезон 2023/24**")

# Загрузка данных
players_df = load_players_list()
all_stats = load_all_stats()

# Боковая панель
st.sidebar.header("🔍 Сравнение игроков")
player_options = {row['player_name']: row['player_id'] for _, row in players_df.iterrows()}
player_names = list(player_options.keys())

player1 = st.sidebar.selectbox("Игрок 1", player_names, index=0)
player2 = st.sidebar.selectbox("Игрок 2", player_names, index=min(1, len(player_names)-1))

# --- Сравнение двух игроков ---
st.subheader(f"📊 Сравнение: {player1} vs {player2}")

stats1 = load_player_stats(player_options[player1])
stats2 = load_player_stats(player_options[player2])

if stats1 is not None and stats2 is not None:
    compare_df = pd.DataFrame({
        'Метрика': ['Команда', 'Позиция', 'Матчи', 'Голы', 'Передачи', 'xG', 'xA'],
        player1: [
            stats1['team_name'], stats1['position'], stats1['matches'],
            stats1['goals'], stats1['assists'], stats1['xg'], stats1['xa']
        ],
        player2: [
            stats2['team_name'], stats2['position'], stats2['matches'],
            stats2['goals'], stats2['assists'], stats2['xg'], stats2['xa']
        ]
    })
    st.dataframe(compare_df, use_container_width=True)

    # График сравнения
    fig_compare = px.bar(
        compare_df[compare_df['Метрика'].isin(['Голы', 'Передачи', 'xG', 'xA'])],
        x='Метрика', y=[player1, player2], barmode='group',
        title=f"Сравнение статистики: {player1} vs {player2}"
    )
    st.plotly_chart(fig_compare, use_container_width=True)

# --- Общая статистика ---
st.subheader("🏆 Топ-10 бомбардиров лиги")
top_scorers = all_stats.nlargest(10, 'goals')
fig1 = px.bar(top_scorers, x='goals', y='player_name', color='team_name',
              orientation='h', title='Лучшие бомбардиры', text='goals')
fig1.update_traces(textposition='outside')
st.plotly_chart(fig1, use_container_width=True)

st.subheader("✨ Голы vs Ожидаемые голы (xG)")
fig2 = px.scatter(all_stats, x='xg', y='goals', size='matches', color='team_name',
                  hover_name='player_name', text='player_name',
                  title="Реальные голы vs xG")
fig2.update_traces(textposition='top center')
st.plotly_chart(fig2, use_container_width=True)

st.subheader("📋 Полная таблица игроков")
st.dataframe(all_stats, use_container_width=True)