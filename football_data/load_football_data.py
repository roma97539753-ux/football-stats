import sqlite3
import pandas as pd
import numpy as np

print("📥 Загрузка данных в базу данных...")

# Читаем CSV-файлы
teams_df = pd.read_csv('teams.csv')
players_df = pd.read_csv('players.csv')
players_stats_df = pd.read_csv('playerstats.csv')

print(f"✅ Загружено команд: {len(teams_df)}")
print(f"✅ Загружено игроков: {len(players_df)}")
print(f"✅ Загружено записей статистики: {len(players_stats_df)}")

# Подключаемся к БД
conn = sqlite3.connect('football_stats.db')
cursor = conn.cursor()

# Создаем таблицы
cursor.execute('DROP TABLE IF EXISTS teams')
cursor.execute('DROP TABLE IF EXISTS players')
cursor.execute('DROP TABLE IF EXISTS player_stats')

# Таблица команд
cursor.execute('''
    CREATE TABLE teams (
        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
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

# Таблица игроков
cursor.execute('''
    CREATE TABLE players (
        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        team TEXT,
        position TEXT,
        now_cost REAL,
        selected_by_percent REAL,
        form REAL,
        points_per_game REAL
    )
''')

# Таблица статистики игроков
cursor.execute('''
    CREATE TABLE player_stats (
        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        goals INTEGER,
        assists INTEGER,
        expected_goals REAL,
        expected_assists REAL,
        minutes INTEGER,
        influence REAL,
        creativity REAL,
        threat REAL,
        bonus INTEGER,
        bps INTEGER,
        gw INTEGER,
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    )
''')

# Заполняем команды
for _, row in teams_df.iterrows():
    cursor.execute('''
        INSERT INTO teams (name, short_name, strength, strength_attack_home, 
                          strength_attack_away, strength_defence_home, 
                          strength_defence_away, elo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row['name'], row['short_name'], row['strength'],
          row['strength_attack_home'], row['strength_attack_away'],
          row['strength_defence_home'], row['strength_defence_away'],
          row['elo']))

# Заполняем игроков
for _, row in players_df.iterrows():
    cursor.execute('''
        INSERT INTO players (name, team, position, now_cost, selected_by_percent, form, points_per_game)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (row['name'], row['team'], row.get('element_type', 'Unknown'),
          row['now_cost'], row['selected_by_percent'], row['form'], row['points_per_game']))
    
    player_id = cursor.lastrowid
    
    # Ищем статистику для этого игрока
    player_stats = players_stats_df[players_stats_df['id'] == row['id']]
    for _, stat_row in player_stats.iterrows():
        cursor.execute('''
            INSERT INTO player_stats (player_id, goals, assists, expected_goals, expected_assists,
                                      minutes, influence, creativity, threat, bonus, bps, gw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (player_id, stat_row.get('goals_scored', 0), stat_row.get('assists', 0),
              stat_row.get('expected_goals', 0), stat_row.get('expected_assists', 0),
              stat_row.get('minutes', 0), stat_row.get('influence', 0),
              stat_row.get('creativity', 0), stat_row.get('threat', 0),
              stat_row.get('bonus', 0), stat_row.get('bps', 0), stat_row.get('gw', 0)))

conn.commit()
conn.close()

print("\n✅ База данных успешно создана!")
print("   Таблицы: teams, players, player_stats")