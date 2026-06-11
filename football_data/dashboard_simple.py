import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

st.set_page_config(page_title="Футбольная аналитика АПЛ", layout="wide")

st.title("⚽ Футбольная аналитика АПЛ")
st.markdown("**Сезон 2025/26 | Данные: FPL Stats**")

# Подключение к БД - одно соединение на всё приложение
@st.cache_resource
def get_connection():
    return sqlite3.connect('football_stats_ready.db', check_same_thread=False)

# Загружаем игроков
@st.cache_data
def load_players():
    conn = get_connection()
    try:
        # Сначала проверим, какие колонки есть
        df_sample = pd.read_sql_query("SELECT * FROM players LIMIT 1", conn)
        available_cols = df_sample.columns.tolist()
        
        # Загружаем все данные
        df = pd.read_sql_query("SELECT * FROM players", conn)
        
        # Конвертируем числовые колонки
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        
        return df, available_cols
    except Exception as e:
        st.error(f"Ошибка загрузки игроков: {e}")
        return pd.DataFrame(), []
    # НЕ закрываем соединение здесь

# Загружаем команды
@st.cache_data
def load_teams():
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM teams", conn)
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки команд: {e}")
        return pd.DataFrame()
    # НЕ закрываем соединение здесь

# Загружаем данные
players_df, available_cols = load_players()
teams_df = load_teams()

# Показываем статус
if len(players_df) > 0:
    st.sidebar.success(f"✅ Загружено {len(players_df)} игроков")
else:
    st.sidebar.error("❌ Нет данных об игроках")

if len(teams_df) > 0:
    st.sidebar.success(f"✅ Загружено {len(teams_df)} команд")

# ========== ГЛАВНАЯ СТРАНИЦА ==========

# Основные метрики
if len(players_df) > 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏃 Всего игроков", len(players_df))
    with col2:
        if 'goals' in players_df.columns:
            goals_sum = pd.to_numeric(players_df['goals'], errors='coerce').fillna(0).sum()
            st.metric("⚽ Всего голов", int(goals_sum))
    with col3:
        if 'assists' in players_df.columns:
            assists_sum = pd.to_numeric(players_df['assists'], errors='coerce').fillna(0).sum()
            st.metric("🎯 Всего передач", int(assists_sum))

# Таблица с данными
st.subheader("📋 Данные игроков")
if len(players_df) > 0:
    # Выбираем основные колонки для отображения
    display_cols = ['web_name', 'team_name', 'position', 'goals', 'assists', 'minutes', 'now_cost', 'form']
    existing_cols = [col for col in display_cols if col in players_df.columns]
    if existing_cols:
        st.dataframe(players_df[existing_cols].head(50), use_container_width=True)
    else:
        st.dataframe(players_df.head(20), use_container_width=True)
else:
    st.info("Нет данных для отображения")

# График бомбардиров
if 'goals' in players_df.columns and 'web_name' in players_df.columns:
    st.subheader("🏆 Топ-10 бомбардиров")
    players_df['goals'] = pd.to_numeric(players_df['goals'], errors='coerce').fillna(0)
    top_scorers = players_df.nlargest(10, 'goals')
    
    if len(top_scorers) > 0 and top_scorers['goals'].sum() > 0:
        fig = px.bar(top_scorers, x='goals', y='web_name', 
                     title='Лучшие бомбардиры',
                     orientation='h', text='goals',
                     color_discrete_sequence=['blue'])
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Нет данных о голах")

# Команды
if len(teams_df) > 0:
    st.subheader("🏆 Команды")
    st.dataframe(teams_df, use_container_width=True)

# Информация о колонках
with st.expander("📋 Доступные колонки в базе данных"):
    st.write(available_cols)