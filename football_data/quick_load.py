import sqlite3
import pandas as pd

print("📥 Загрузка данных...")

# Читаем CSV
players_df = pd.read_csv('players.csv')
print(f"✅ players.csv: {len(players_df)} строк")

# Подключаемся к БД
conn = sqlite3.connect('football_stats.db')
cursor = conn.cursor()

# Создаём таблицу
cursor.execute('DROP TABLE IF EXISTS players')
cursor.execute('''
    CREATE TABLE players (
        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
        web_name TEXT,
        first_name TEXT,
        second_name TEXT,
        team_name TEXT,
        position TEXT,
        minutes INTEGER DEFAULT 0,
        goals INTEGER DEFAULT 0,
        assists INTEGER DEFAULT 0,
        expected_goals REAL DEFAULT 0,
        expected_assists REAL DEFAULT 0,
        now_cost REAL DEFAULT 0,
        form REAL DEFAULT 0
    )
''')

# Заполняем данными
for _, row in players_df.iterrows():
    cursor.execute('''
        INSERT INTO players (web_name, first_name, second_name, team_name, position,
                            minutes, goals, assists, now_cost, form)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        row.get('web_name', ''),
        row.get('first_name', ''),
        row.get('second_name', ''),
        row.get('team', 'Unknown'),
        row.get('position', ''),
        0,  # minutes временно 0, потом обновим из playerstats
        0,  # goals временно 0
        0,  # assists временно 0
        float(row.get('now_cost', 0)) if pd.notna(row.get('now_cost', 0)) else 0,
        float(row.get('form', 0)) if pd.notna(row.get('form', 0)) else 0
    ))

conn.commit()

# Проверка
cursor.execute("SELECT COUNT(*) FROM players")
count = cursor.fetchone()[0]
print(f"✅ Загружено {count} игроков")

conn.close()