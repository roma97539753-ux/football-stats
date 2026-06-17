cat > create_final_db.py << 'EOF'
import sqlite3
import pandas as pd
import random

print(" СОЗДАНИЕ БАЗЫ ДАННЫХ")

# Читаем файлы
players_csv = pd.read_csv('players.csv')
teams_csv = pd.read_csv('teams.csv')
playerstats_df = pd.read_csv('playerstats.csv')

print(f"✅ players.csv: {len(players_csv)} записей")
print(f"✅ teams.csv: {len(teams_csv)} записей")

# Суммируем ожидаемые голы
expected_stats = {}
for _, row in playerstats_df.iterrows():
    pid = row['id']
    if pid not in expected_stats:
        expected_stats[pid] = {'expected_goals': 0, 'expected_assists': 0, 'form': 0, 'now_cost': 0}
    expected_stats[pid]['expected_goals'] += row.get('expected_goals', 0) or 0
    expected_stats[pid]['expected_assists'] += row.get('expected_assists', 0) or 0
    expected_stats[pid]['form'] = row.get('form', 0) or 0
    expected_stats[pid]['now_cost'] = row.get('now_cost', 0) or 0

# Создаем демо-данные
random.seed(42)
demo_players = []
for _, row in players_csv.iterrows():
    pid = row['player_id']
    exp = expected_stats.get(pid, {})
    expected_goals = exp.get('expected_goals', 0)
    
    if expected_goals > 0:
        goals = int(round(expected_goals * random.uniform(0.7, 1.3)))
        assists = int(round(exp.get('expected_assists', 0) * random.uniform(0.7, 1.3)))
        minutes = random.randint(1500, 3400) if expected_goals > 2 else random.randint(500, 1800)
    else:
        pos = row.get('position', 'Midfielder')
        if pos == 'Forward':
            goals, assists, minutes = random.randint(5, 20), random.randint(2, 12), random.randint(1500, 3200)
        elif pos == 'Midfielder':
            goals, assists, minutes = random.randint(2, 12), random.randint(3, 15), random.randint(1500, 3300)
        elif pos == 'Defender':
            goals, assists, minutes = random.randint(0, 6), random.randint(0, 8), random.randint(1500, 3420)
        else:
            goals, assists, minutes = 0, random.randint(0, 3), random.randint(900, 3420)
    
    demo_players.append({
        'player_id': pid,
        'web_name': row['web_name'],
        'team_name': row.get('team', 'Unknown'),
        'position': row.get('position', 'Midfielder'),
        'goals': goals,
        'assists': assists,
        'minutes': minutes,
        'expected_goals': round(expected_goals, 1),
        'expected_assists': round(exp.get('expected_assists', 0), 1),
        'form': round(exp.get('form', random.uniform(2, 8)), 1),
        'now_cost': exp.get('now_cost', random.uniform(4, 12))
    })

# Создаем БД
conn = sqlite3.connect('football_stats_ready.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS players')
cursor.execute('''
    CREATE TABLE players (
        player_id INTEGER PRIMARY KEY,
        web_name TEXT,
        team_name TEXT,
        position TEXT,
        goals INTEGER,
        assists INTEGER,
        minutes INTEGER,
        expected_goals REAL,
        expected_assists REAL,
        form REAL,
        now_cost REAL
    )
''')

for p in demo_players:
    cursor.execute('''
        INSERT INTO players (player_id, web_name, team_name, position, goals, assists, minutes, expected_goals, expected_assists, form, now_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (p['player_id'], p['web_name'], p['team_name'], p['position'], p['goals'], p['assists'], p['minutes'], p['expected_goals'], p['expected_assists'], p['form'], p['now_cost']))

cursor.execute('DROP TABLE IF EXISTS teams')
cursor.execute('''
    CREATE TABLE teams (
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

for _, row in teams_csv.iterrows():
    cursor.execute('''
        INSERT OR REPLACE INTO teams (code, name, short_name, strength, strength_attack_home, strength_attack_away, strength_defence_home, strength_defence_away, elo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row['code'], row['name'], row['short_name'], row['strength'], row['strength_attack_home'], row['strength_attack_away'], row['strength_defence_home'], row['strength_defence_away'], row['elo']))

conn.commit()

cursor.execute("SELECT COUNT(*) FROM players")
print(f"\n✅ Игроков: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM teams")
print(f"✅ Команд: {cursor.fetchone()[0]}")

cursor.execute("SELECT web_name, goals FROM players ORDER BY goals DESC LIMIT 10")
print("\n🏆 Топ-10 бомбардиров:")
for name, goals in cursor.fetchall():
    print(f"   {name}: {goals} голов")

conn.close()
print("\n✅ Готово! Запускайте: streamlit run dashboard_full.py")
EOF