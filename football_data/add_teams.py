import sqlite3
import pandas as pd

print("📥 Добавление таблицы команд в базу данных...")

# Читаем teams.csv
teams_df = pd.read_csv('teams.csv')
print(f"✅ teams.csv: {len(teams_df)} команд")

# Подключаемся к существующей БД
conn = sqlite3.connect('football_stats_ready.db')
cursor = conn.cursor()

# Создаем таблицу команд
cursor.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        code INTEGER PRIMARY KEY,
        name TEXT,
        short_name TEXT,
        strength INTEGER,
        strength_attack_home REAL,
        strength_attack_away REAL,
        strength_defence_home REAL,
        strength_defence_away REAL,
        elo INTEGER
    )
''')

# Заполняем данными
for _, row in teams_df.iterrows():
    cursor.execute('''
        INSERT OR REPLACE INTO teams (code, name, short_name, strength, 
                                     strength_attack_home, strength_attack_away,
                                     strength_defence_home, strength_defence_away, elo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row['code'], row['name'], row['short_name'], row['strength'],
          row['strength_attack_home'], row['strength_attack_away'],
          row['strength_defence_home'], row['strength_defence_away'],
          row['elo']))

conn.commit()

# Проверка
cursor.execute("SELECT COUNT(*) FROM teams")
count = cursor.fetchone()[0]
print(f"✅ Добавлено {count} команд")

# Покажем список
cursor.execute("SELECT name, strength, elo FROM teams ORDER BY strength DESC")
teams = cursor.fetchall()
print("\n🏆 Команды АПЛ 2025/26:")
for name, strength, elo in teams:
    print(f"   {name}: сила={strength}, рейтинг={elo}")

conn.close()
print("\n✅ Готово! Теперь перезапустите дашборд.")