import sqlite3
import pandas as pd

print("📥 Обновление статистики игроков...")

# Читаем playerstats.csv
playerstats_df = pd.read_csv('playerstats.csv')
print(f"✅ playerstats.csv: {len(playerstats_df)} записей")

# Суммируем статистику по каждому игроку
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

# Подключаемся к БД
conn = sqlite3.connect('football_stats.db')
cursor = conn.cursor()

# Получаем всех игроков с их player_code
cursor.execute("SELECT rowid, player_code, web_name FROM players")
players = cursor.fetchall()

updated = 0
for rowid, player_code, web_name in players:
    if player_code in stats_by_player:
        stats = stats_by_player[player_code]
        cursor.execute('''
            UPDATE players 
            SET minutes = ?, goals = ?, assists = ?, expected_goals = ?, expected_assists = ?
            WHERE rowid = ?
        ''', (stats['minutes'], stats['goals'], stats['assists'], 
              stats['expected_goals'], stats['expected_assists'], rowid))
        updated += 1

conn.commit()
print(f"✅ Обновлено {updated} игроков")

# Проверка
cursor.execute("SELECT web_name, goals, minutes FROM players WHERE goals > 0 ORDER BY goals DESC LIMIT 10")
top_scorers = cursor.fetchall()
print("\n🏆 Топ-10 бомбардиров:")
for name, goals, minutes in top_scorers:
    print(f"   {name}: {goals} голов ({minutes} минут)")

conn.close()
print("\n✅ Готово! Теперь перезапустите дашборд.")