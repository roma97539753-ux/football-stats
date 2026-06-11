import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Настройка страницы
st.set_page_config(page_title="Анализ футбольной статистики АПЛ", layout="wide")

# Заголовок
st.title("⚽ Анализ футбольной статистики АПЛ")
st.markdown("**Данные сезона 2023/24** (топ-игроки лиги)")
st.markdown("---")

# Загрузка данных
@st.cache_data
def load_data():
    df = pd.read_csv('epl_data.csv')
    # Преобразуем числовые колонки
    for col in ['Goals', 'Assists', 'Matches', 'xG', 'xA']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

df = load_data()

# Боковая панель с фильтрами
st.sidebar.header("🔍 Фильтры")

# Получаем уникальные значения для фильтров
teams = ['Все'] + sorted(df['Team'].unique().tolist())
positions = ['Все'] + sorted(df['Position'].unique().tolist())

selected_team = st.sidebar.selectbox("Команда", teams)
selected_position = st.sidebar.selectbox("Позиция", positions)

# Применяем фильтры
filtered_df = df.copy()
if selected_team != 'Все':
    filtered_df = filtered_df[filtered_df['Team'] == selected_team]
if selected_position != 'Все':
    filtered_df = filtered_df[filtered_df['Position'] == selected_position]

# Основные метрики
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("🏃 Игроков", len(filtered_df))
with col2:
    st.metric("⚽ Всего голов", filtered_df['Goals'].sum())
with col3:
    st.metric("🎯 Всего передач", filtered_df['Assists'].sum())
with col4:
    st.metric("📊 Средний xG", f"{filtered_df['xG'].mean():.1f}")
with col5:
    st.metric("🎭 Средний xA", f"{filtered_df['xA'].mean():.1f}")

st.markdown("---")

# График 1: Топ бомбардиров
st.subheader("🏆 Топ бомбардиров сезона")
top_scorers = filtered_df.nlargest(10, 'Goals')
fig1 = px.bar(top_scorers,
              x='Goals',
              y='Player',
              color='Team',
              orientation='h',
              title='Лучшие бомбардиры',
              text='Goals',
              height=500)
fig1.update_traces(textposition='outside')
st.plotly_chart(fig1, use_container_width=True)

# График 2: Голы vs xG
st.subheader("✨ Эффективность: Голы vs Ожидаемые голы (xG)")
fig2 = px.scatter(filtered_df,
                  x='xG',
                  y='Goals',
                  size='Matches',
                  color='Team',
                  hover_name='Player',
                  text='Player',
                  title="Сравнение реальных голов с ожидаемыми",
                  labels={'xG': 'Ожидаемые голы (xG)', 'Goals': 'Реальные голы'})
fig2.update_traces(textposition='top center')
fig2.update_layout(height=500)
st.plotly_chart(fig2, use_container_width=True)

# Таблица с данными
st.subheader("📋 Подробная статистика игроков")
st.dataframe(filtered_df[['Player', 'Team', 'Position', 'Goals', 'Assists', 'Matches', 'xG', 'xA']],
             use_container_width=True)

# Аналитический вывод
st.markdown("---")
st.subheader("📈 Аналитический вывод")

total_goals = filtered_df['Goals'].sum()
total_xg = filtered_df['xG'].sum()
efficiency = (total_goals / total_xg * 100) if total_xg > 0 else 0

st.markdown(f"""
- **Всего голов:** {total_goals}
- **Суммарный xG:** {total_xg:.1f}
- **Эффективность реализации:** {efficiency:.1f}%
""")

if efficiency > 100:
    st.success("✅ Игроки забивают больше ожидаемого — отличная реализация моментов!")
elif efficiency < 100:
    st.warning("⚠️ Игроки забивают меньше ожидаемого — нужно работать над реализацией")
else:
    st.info("📊 Реализация моментов на уровне ожиданий")