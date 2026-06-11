import sqlite3
import pandas as pd

print("📥 Обновление статистики игроков...")

# Читаем players.csv (связь player_id с web_name)
players_csv = pd.read_csv('players.csv')
print(f"✅ players.csv: {len(players_csv)} записей")

# Читаем playerstats.csv (статистика)
playerstats_df = pd.read_csv('playerstats.csv')
print(f"✅ playerstats.csv: {len(playerstats_df)} записей")

# Суммируем статистику по каждому игроку (по id из playerstats)
stats_by_player = {}
for _, row in playerstats_df.iterrows():
    pid = row['id']
    if pid not in stats_by_player:
        stats_by_player[pid] = {
            'minutes': 0,
            'goals': 0,
            'assists': 0,
            'expected_goals': 0,
            'expected_assists': 0
        }
    
    # Суммируем
    stats_by_player[pid]['minutes'] += int(row.get('minutes', 0)) if pd.notna(row.get('minutes', 0)) else 0
    stats_by_player[pid]['goals'] += int(row.get('goals_scored', 0)) if pd.notna(row.get('goals_scored', 0)) else 0
    stats_by_player[pid]['assists'] += int(row.get('assists', 0)) if pd.notna(row.get('assists', 0)) else 0
    stats_by_player[pid]['expected_goals'] += float(row.get('expected_goals', 0)) if pd.notna(row.get('expected_goals', 0)) else 0
    stats_by_player[pid]['expected_assists'] += float(row.get('expected_assists', 0)) if pd.notna(row.get('expected_assists', 0)) else 0

print(f"✅ Собрана статистика для {len(stats_by_player)} игроков")

# Создаем словарь: player_id (из players.csv) -> web_name
csv_player_map = {}
for _, row in players_csv.iterrows():
    csv_player_map[row['player_id']] = row['web_name']

print(f"✅ Сопоставлено {len(csv_player_map)} игроков")

# Подключаемся к БД
conn = sqlite3.connect('football_stats.db')
cursor = conn.cursor()

# Обновляем статистику
updated = 0
for player_id, web_name in csv_player_map.items():
    if player_id in stats_by_player:
        stats = stats_by_player[player_id]
        cursor.execute('''
            UPDATE players 
            SET minutes = ?, goals = ?, assists = ?, expected_goals = ?, expected_assists = ?
            WHERE web_name = ?
        ''', (stats['minutes'], stats['goals'], stats['assists'], 
              stats['expected_goals'], stats['expected_assists'], web_name))
        updated += cursor.rowcount

conn.commit()
print(f"✅ Обновлено {updated} игроков")

# Проверка: топ бомбардиров
cursor.execute("SELECT web_name, goals, minutes FROM players WHERE goals > 0 ORDER BY goals DESC LIMIT 10")
top_scorers = cursor.fetchall()
print("\n🏆 Топ-10 бомбардиров:")
if top_scorers:
    for name, goals, minutes in top_scorers:
        print(f"   {name}: {goals} голов ({minutes} минут)")
else:
    print("   Нет данных о голах")
    
    # Покажем первых 5 игроков с их данными
    cursor.execute("SELECT web_name, goals, minutes FROM players LIMIT 5")
    sample = cursor.fetchall()
    print("\n📊 Пример данных из БД:")
    for name, goals, minutes in sample:
        print(f"   {name}: goals={goals}, minutes={minutes}")

conn.close()
print("\n✅ Готово! Теперь перезапустите дашборд.")