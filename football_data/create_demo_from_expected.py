import sqlite3
import pandas as pd
import random

print("📥 Создание демонстрационных данных на основе expected_goals...")

# Читаем файлы
players_df = pd.read_csv('players.csv')
playerstats_df = pd.read_csv('playerstats.csv')
teams_df = pd.read_csv('teams.csv')

print(f"✅ players.csv: {len(players_df)} игроков")
print(f"✅ playerstats.csv: {len(playerstats_df)} записей")

# Создаем словарь команд для быстрого доступа
team_names = {row['code']: row['name'] for _, row in teams_df.iterrows()}

# Суммируем ожидаемые голы по каждому игроку
expected_stats = {}
for _, row in playerstats_df.iterrows():
    pid = row['id']
    if pid not in expected_stats:
        expected_stats[pid] = {
            'expected_goals': 0,
            'expected_assists': 0,
            'influence': 0,
            'creativity': 0,
            'threat': 0,
            'form': 0,
            'now_cost': 0
        }
    
    expected_stats[pid]['expected_goals'] += row.get('expected_goals', 0) or 0
    expected_stats[pid]['expected_assists'] += row.get('expected_assists', 0) or 0
    expected_stats[pid]['influence'] = row.get('influence', 0) or 0
    expected_stats[pid]['creativity'] = row.get('creativity', 0) or 0
    expected_stats[pid]['threat'] = row.get('threat', 0) or 0
    expected_stats[pid]['form'] = row.get('form', 0) or 0
    expected_stats[pid]['now_cost'] = row.get('now_cost', 0) or 0

print(f"✅ Собраны ожидаемые показатели для {len(expected_stats)} игроков")

# Создаем демо-данные на основе expected_goals
random.seed(42)
demo_data = []

for _, row in players_df.iterrows():
    pid = row['player_id']
    exp = expected_stats.get(pid, {})
    
    # Реальные голы примерно равны ожидаемым с небольшим отклонением
    expected_goals = exp.get('expected_goals', 0)
    expected_assists = exp.get('expected_assists', 0)
    
    # Генерируем реалистичные данные
    if expected_goals > 0:
        goals = max(0, int(round(expected_goals * random.uniform(0.7, 1.3))))
    else:
        goals = random.randint(0, 3) if row.get('position') == 'Forward' else random.randint(0, 1)
    
    if expected_assists > 0:
        assists = max(0, int(round(expected_assists * random.uniform(0.7, 1.3))))
    else:
        assists = random.randint(0, 5) if row.get('position') in ['Forward', 'Midfielder'] else random.randint(0, 2)
    
    # Минуты: если есть expected_goals > 0, значит игрок играет много
    if expected_goals > 2:
        minutes = random.randint(2000, 3400)
    elif expected_goals > 0:
        minutes = random.randint(800, 2200)
    else:
        minutes = random.randint(100, 1000)
    
    # Имя команды
    team_code = row.get('team_code')
    team_name = team_names.get(team_code, 'Unknown')
    if team_name == 'Unknown':
        team_name = row.get('team', 'Unknown')
    
    demo_data.append({
        'player_id': pid,
        'web_name': row['web_name'],
        'first_name': row.get('first_name', ''),
        'second_name': row.get('second_name', ''),
        'team_name': team_name,
        'position': row.get('position', 'Midfielder'),
        'goals': goals,
        'assists': assists,
        'minutes': minutes,
        'expected_goals': round(expected_goals, 1),
        'expected_assists': round(expected_assists, 1),
        'now_cost': exp.get('now_cost', 5.0),
        'form': exp.get('form', 5.0),
        'influence': exp.get('influence', 0),
        'creativity': exp.get('creativity', 0),
        'threat': exp.get('threat', 0)
    })

# Создаем базу данных
conn = sqlite3.connect('football_stats_ready.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE players (
        player_id INTEGER PRIMARY KEY,
        web_name TEXT,
        first_name TEXT,
        second_name TEXT,
        team_name TEXT,
        position TEXT,
        goals INTEGER,
        assists INTEGER,
        minutes INTEGER,
        expected_goals REAL,
        expected_assists REAL,
        now_cost REAL,
        form REAL,
        influence REAL,
        creativity REAL,
        threat REAL
    )
''')

for data in demo_data:
    cursor.execute('''
        INSERT INTO players (player_id, web_name, first_name, second_name, team_name, 
                            position, goals, assists, minutes, expected_goals, expected_assists,
                            now_cost, form, influence, creativity, threat)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['player_id'], data['web_name'], data['first_name'], data['second_name'],
          data['team_name'], data['position'], data['goals'], data['assists'], data['minutes'],
          data['expected_goals'], data['expected_assists'], data['now_cost'], data['form'],
          data['influence'], data['creativity'], data['threat']))

conn.commit()

# Проверка
cursor.execute("SELECT web_name, team_name, goals, assists, expected_goals FROM players WHERE goals > 0 ORDER BY goals DESC LIMIT 15")
top_scorers = cursor.fetchall()
print("\n🏆 Топ-15 бомбардиров (на основе ожидаемых голов):")
for name, team, goals, assists, xg in top_scorers:
    print(f"   {name} ({team}): {goals} голов, {assists} передач, xG={xg}")

cursor.execute("SELECT COUNT(*) FROM players")
count = cursor.fetchone()[0]
print(f"\n✅ Создана база football_stats_ready.db с {count} игроками")
conn.close()

print("\n🎉 Теперь запустите дашборд с этой базой!")