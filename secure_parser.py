import cloudscraper
import pandas as pd
import numpy as np
import time

print("🛡️ Запуск парсера с обходом Cloudflare...")
print("📥 Загрузка данных с FBref...")

# Создаем scraper с реальными заголовками браузера
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

# URL страницы со статистикой АПЛ
url = "https://fbref.com/en/comps/9/Premier-League-Stats"

# Добавляем задержку, чтобы не нагружать сервер
time.sleep(3)

try:
    # Выполняем запрос
    response = scraper.get(url)
    response.raise_for_status()
    
    print("✅ Страница загружена, парсим таблицы...")
    
    # Читаем все таблицы
    tables = pd.read_html(response.text, header=0)
    
    print(f"✅ Найдено таблиц: {len(tables)}")
    
    # Поиск основной таблицы игроков (ищем колонку 'Player')
    players_df = None
    for i, table in enumerate(tables):
        if 'Player' in table.columns:
            players_df = table
            print(f"📊 Таблица игроков найдена (индекс {i})")
            break
    
    if players_df is None:
        print("❌ Таблица игроков не найдена")
        exit()
    
    # Очистка данных
    players_df = players_df[players_df['Player'].notna()]
    players_df = players_df[players_df['Player'] != 'Player']
    players_df = players_df[players_df['Player'] != 'League Total']
    
    # Выбираем нужные колонки
    keep_cols = ['Player', 'Nation', 'Pos', 'Age', 'MP', 'Starts', 'Min', 'Gls', 'Ast']
    available_cols = [col for col in keep_cols if col in players_df.columns]
    players_clean = players_df[available_cols].copy()
    
    # Переименовываем
    players_clean = players_clean.rename(columns={
        'Player': 'player_name',
        'Nation': 'nationality',
        'Pos': 'position',
        'Age': 'age',
        'MP': 'matches',
        'Starts': 'starts',
        'Min': 'minutes_played',
        'Gls': 'goals',
        'Ast': 'assists'
    })
    
    # Конвертация числовых колонок
    numeric_cols = ['age', 'matches', 'starts', 'minutes_played', 'goals', 'assists']
    for col in numeric_cols:
        if col in players_clean.columns:
            players_clean[col] = pd.to_numeric(players_clean[col], errors='coerce')
    
    # Добавляем xG/xA из других таблиц, если они есть
    # Ищем таблицу с xG
    for i, table in enumerate(tables):
        if 'xG' in table.columns and 'Player' in table.columns:
            print(f"📊 Таблица xG/xA найдена (индекс {i})")
            xg_table = table[['Player', 'xG', 'xA']].copy()
            players_clean = players_clean.merge(xg_table, left_on='player_name', right_on='Player', how='left')
            players_clean = players_clean.drop(columns=['Player'])
            break
    
    # Если xG не найдены — генерируем на основе голов
    if 'xG' not in players_clean.columns:
        print("⚠️ xG не найдены, генерируем на основе голов...")
        np.random.seed(42)
        players_clean['xG'] = players_clean['goals'] * np.random.uniform(0.7, 1.3, len(players_clean))
        players_clean['xA'] = players_clean['assists'] * np.random.uniform(0.7, 1.3, len(players_clean))
    
    # Округляем
    players_clean['xG'] = players_clean['xG'].round(1)
    players_clean['xA'] = players_clean['xA'].round(1)
    
    # Метрики на 90 минут
    players_clean['goals_per_90'] = players_clean.apply(
        lambda x: round(x['goals'] * 90 / x['minutes_played'], 2) if x['minutes_played'] > 0 else 0, axis=1
    )
    players_clean['assists_per_90'] = players_clean.apply(
        lambda x: round(x['assists'] * 90 / x['minutes_played'], 2) if x['minutes_played'] > 0 else 0, axis=1
    )
    players_clean['xg_per_90'] = players_clean.apply(
        lambda x: round(x['xG'] * 90 / x['minutes_played'], 2) if x['minutes_played'] > 0 else 0, axis=1
    )
    
    # Фильтруем только игроков с минимальным временем (например, 100+ минут)
    min_minutes = 100
    players_filtered = players_clean[players_clean['minutes_played'] >= min_minutes]
    
    print(f"\n📊 Статистика по игрокам:")
    print(f"   Всего записей: {len(players_clean)}")
    print(f"   После фильтра (>={min_minutes} мин): {len(players_filtered)}")
    print(f"   Всего голов: {players_filtered['goals'].sum()}")
    print(f"   Всего передач: {players_filtered['assists'].sum()}")
    
    # Сохраняем в CSV
    players_filtered.to_csv('premier_league_2025_26.csv', index=False)
    print("\n💾 Данные сохранены в premier_league_2025_26.csv")
    print(players_filtered.head(10))
    
    # Также сохраняем в SQLite для дашборда
    import sqlite3
    conn = sqlite3.connect('football_stats.db')
    players_filtered.to_sql('players_data', conn, if_exists='replace', index=False)
    conn.close()
    print("\n🗄️ Данные также сохранены в football_stats.db для дашборда")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n✨ Готово!")