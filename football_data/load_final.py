import sqlite3
import pandas as pd

print("📥 Загрузка данных в базу данных...")

# Читаем CSV-файлы
teams_df = pd.read_csv('teams.csv')
players_df = pd.read_csv('players.csv')
playerstats_df = pd.read_csv('playerstats.csv')

print(f"✅ Загружено команд: {len(teams_df)}")
print(f"✅ Загружено игроков: {len(players_df)}")
print(f"✅ Загружено записей статистики: {len(playerstats_df)}")

# Создаем словарь team_code -> team_name для связи
team_code_to_name = {}
for _, row in teams_df.iterrows():
    team_code_to_name[row['code']] = row['name']

# Создаем словарь статистики по player_id
stats_by_player = {}
for _, row in playerstats_df.iterrows():
    pid = row['id']
    if pid not in stats_by_player:
        stats_by_player[pid] = []
    stats_by_player[pid].append(row)

# Подключаемся к БД
conn = sqlite3.connect('football_stats.db')
cursor = conn.cursor()

# Создаем таблицы
cursor.execute('DROP TABLE IF EXISTS teams')
cursor.execute('DROP TABLE IF EXISTS players')
cursor.execute('DROP TABLE IF EXISTS player_stats')

# --- ТАБЛИЦА КОМАНД ---
cursor.execute('''
    CREATE TABLE teams (
        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
        code INTEGER,
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

# Заполняем команды
for _, row in teams_df.iterrows():
    cursor.execute('''
        INSERT INTO teams (code, name, short_name, strength, 
                          strength_attack_home, strength_attack_away,
                          strength_defence_home, strength_defence_away, elo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row['code'], row['name'], row['short_name'], row['strength'],
          row['strength_attack_home'], row['strength_attack_away'],
          row['strength_defence_home'], row['strength_defence_away'],
          row['elo']))

# --- ТАБЛИЦА ИГРОКОВ ---
cursor.execute('''
    CREATE TABLE players (
        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_code INTEGER,
        first_name TEXT,
        second_name TEXT,
        web_name TEXT,
        team_name TEXT,
        position TEXT,
        now_cost REAL,
        selected_by_percent REAL,
        total_points INTEGER,
        points_per_game REAL,
        form REAL,
        minutes INTEGER,
        goals INTEGER,
        assists INTEGER,
        expected_goals REAL,
        expected_assists REAL,
        influence REAL,
        creativity REAL,
        threat REAL,
        ict_index REAL,
        bonus INTEGER,
        bps INTEGER
    )
''')

# Заполняем игроков (объединяя с данными из playerstats)
for _, row in players_df.iterrows():
    player_code = row['player_code']
    team_code = row['team_code']
    team_name = team_code_to_name.get(team_code, 'Unknown')
    
    # Получаем суммарную статистику из playerstats для этого игрока
    stats_list = stats_by_player.get(row['player_id'], [])
    
    minutes = 0
    goals = 0
    assists = 0
    expected_goals = 0
    expected_assists = 0
    influence = 0
    creativity = 0
    threat = 0
    ict_index = 0
    bonus = 0
    bps = 0
    total_points = 0
    points_per_game = 0
    form = 0
    now_cost = 0
    selected_by_percent = 0
    
    if stats_list:
        # Берем последнюю запись (самую свежую) для основных показателей
        latest = stats_list[-1]
        minutes = int(latest.get('minutes', 0)) if pd.notna(latest.get('minutes', 0)) else 0
        goals = int(latest.get('goals_scored', 0)) if pd.notna(latest.get('goals_scored', 0)) else 0
        assists = int(latest.get('assists', 0)) if pd.notna(latest.get('assists', 0)) else 0
        expected_goals = float(latest.get('expected_goals', 0)) if pd.notna(latest.get('expected_goals', 0)) else 0
        expected_assists = float(latest.get('expected_assists', 0)) if pd.notna(latest.get('expected_assists', 0)) else 0
        influence = float(latest.get('influence', 0)) if pd.notna(latest.get('influence', 0)) else 0
        creativity = float(latest.get('creativity', 0)) if pd.notna(latest.get('creativity', 0)) else 0
        threat = float(latest.get('threat', 0)) if pd.notna(latest.get('threat', 0)) else 0
        ict_index = float(latest.get('ict_index', 0)) if pd.notna(latest.get('ict_index', 0)) else 0
        bonus = int(latest.get('bonus', 0)) if pd.notna(latest.get('bonus', 0)) else 0
        bps = int(latest.get('bps', 0)) if pd.notna(latest.get('bps', 0)) else 0
        total_points = int(latest.get('total_points', 0)) if pd.notna(latest.get('total_points', 0)) else 0
        points_per_game = float(latest.get('points_per_game', 0)) if pd.notna(latest.get('points_per_game', 0)) else 0
        form = float(latest.get('form', 0)) if pd.notna(latest.get('form', 0)) else 0
        now_cost = float(latest.get('now_cost', 0)) if pd.notna(latest.get('now_cost', 0)) else 0
        selected_by_percent = float(latest.get('selected_by_percent', 0)) if pd.notna(latest.get('selected_by_percent', 0)) else 0
    
    cursor.execute('''
        INSERT INTO players (player_code, first_name, second_name, web_name, team_name, position,
                            now_cost, selected_by_percent, total_points, points_per_game, form,
                            minutes, goals, assists, expected_goals, expected_assists,
                            influence, creativity, threat, ict_index, bonus, bps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (player_code, row['first_name'], row['second_name'], row['web_name'],
          team_name, row['position'], now_cost, selected_by_percent,
          total_points, points_per_game, form, minutes, goals, assists,
          expected_goals, expected_assists, influence, creativity, threat,
          ict_index, bonus, bps))

# --- ТАБЛИЦА ПОСТАТУЙНОЙ СТАТИСТИКИ ---
cursor.execute('''
    CREATE TABLE player_stats (
        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_code INTEGER,
        gw INTEGER,
        minutes INTEGER,
        goals_scored INTEGER,
        assists INTEGER,
        expected_goals REAL,
        expected_assists REAL,
        influence REAL,
        creativity REAL,
        threat REAL,
        bonus INTEGER,
        bps INTEGER,
        form REAL,
        value_form REAL
    )
''')

# Заполняем постустатистику
for _, row in playerstats_df.iterrows():
    cursor.execute('''
        INSERT INTO player_stats (player_code, gw, minutes, goals_scored, assists,
                                  expected_goals, expected_assists, influence,
                                  creativity, threat, bonus, bps, form, value_form)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row['id'], row.get('gw', 0), row.get('minutes', 0), row.get('goals_scored', 0),
          row.get('assists', 0), row.get('expected_goals', 0), row.get('expected_assists', 0),
          row.get('influence', 0), row.get('creativity', 0), row.get('threat', 0),
          row.get('bonus', 0), row.get('bps', 0), row.get('form', 0), row.get('value_form', 0)))

conn.commit()
conn.close()

print("\n✅ База данных успешно создана!")
print("   Таблицы: teams, players, player_stats")
print(f"\n📊 Статистика:")
print(f"   Команд: {len(teams_df)}")
print(f"   Игроков: {len(players_df)}")

# Выведем несколько записей для проверки
print("\n📋 Проверка данных (первые 5 игроков):")
conn = sqlite3.connect('football_stats.db')
df_check = pd.read_sql_query("SELECT web_name, team_name, position, goals, assists, expected_goals, minutes FROM players LIMIT 5", conn)
print(df_check)
conn.close()