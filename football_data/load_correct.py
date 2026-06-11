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
        team_code INTEGER,
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

# Заполняем игроков
for _, row in players_df.iterrows():
    # Получаем минуты, голы, ассисты из playerstats
    player_stats = playerstats_df[playerstats_df['id'] == row['player_id']] if 'player_id' in row else None
    
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
    
    if player_stats is not None and len(player_stats) > 0:
        stat = player_stats.iloc[0]
        minutes = int(stat.get('minutes', 0)) if pd.notna(stat.get('minutes', 0)) else 0
        goals = int(stat.get('goals_scored', 0)) if pd.notna(stat.get('goals_scored', 0)) else 0
        assists = int(stat.get('assists', 0)) if pd.notna(stat.get('assists', 0)) else 0
        expected_goals = float(stat.get('expected_goals', 0)) if pd.notna(stat.get('expected_goals', 0)) else 0
        expected_assists = float(stat.get('expected_assists', 0)) if pd.notna(stat.get('expected_assists', 0)) else 0
        influence = float(stat.get('influence', 0)) if pd.notna(stat.get('influence', 0)) else 0
        creativity = float(stat.get('creativity', 0)) if pd.notna(stat.get('creativity', 0)) else 0
        threat = float(stat.get('threat', 0)) if pd.notna(stat.get('threat', 0)) else 0
        ict_index = float(stat.get('ict_index', 0)) if pd.notna(stat.get('ict_index', 0)) else 0
        bonus = int(stat.get('bonus', 0)) if pd.notna(stat.get('bonus', 0)) else 0
        bps = int(stat.get('bps', 0)) if pd.notna(stat.get('bps', 0)) else 0
    
    cursor.execute('''
        INSERT INTO players (player_code, first_name, second_name, web_name, team_code, position,
                            now_cost, selected_by_percent, total_points, points_per_game, form,
                            minutes, goals, assists, expected_goals, expected_assists,
                            influence, creativity, threat, ict_index, bonus, bps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row['player_code'], row['first_name'], row['second_name'], row['web_name'],
          row['team_code'], row['position'], row['now_cost'], row['selected_by_percent'],
          row['total_points'], row['points_per_game'], row['form'], minutes, goals, assists,
          expected_goals, expected_assists, influence, creativity, threat, ict_index, bonus, bps))

# --- ТАБЛИЦА СТАТИСТИКИ ПО ИГРОКАМ (детальная) ---
cursor.execute('''
    CREATE TABLE player_stats (
        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
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
        value_form REAL,
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    )
''')

# Заполняем детальную статистику
for _, row in playerstats_df.iterrows():
    # Находим player_code по id
    player = players_df[players_df['player_id'] == row['id']]
    if len(player) > 0:
        player_code = player.iloc[0]['player_code']
        
        cursor.execute('''
            INSERT INTO player_stats (player_id, gw, minutes, goals_scored, assists,
                                      expected_goals, expected_assists, influence,
                                      creativity, threat, bonus, bps, form, value_form)
            VALUES ((SELECT player_id FROM players WHERE player_code = ?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (player_code, row.get('gw', 0), row.get('minutes', 0), row.get('goals_scored', 0),
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