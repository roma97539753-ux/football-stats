import sqlite3
import pandas as pd


def setup_sqlite_db():
    """Создает БД football_stats.db с тремя таблицами и заполняет данными"""

    # Подключаемся к файлу базы данных (он создастся автоматически)
    conn = sqlite3.connect('football_stats.db')
    cursor = conn.cursor()

    # 1. Таблица команд
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT UNIQUE NOT NULL,
            city TEXT,
            stadium TEXT
        )
    ''')

    # 2. Таблица игроков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            team_id INTEGER,
            position TEXT,
            age INTEGER,
            FOREIGN KEY (team_id) REFERENCES teams (team_id)
        )
    ''')

    # 3. Таблица статистики
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            season TEXT,
            goals INTEGER,
            assists INTEGER,
            matches INTEGER,
            xg REAL,
            xa REAL,
            FOREIGN KEY (player_id) REFERENCES players (player_id)
        )
    ''')

    # Очищаем таблицы перед заполнением (чтобы не было дублей при перезапуске)
    cursor.execute('DELETE FROM player_stats')
    cursor.execute('DELETE FROM players')
    cursor.execute('DELETE FROM teams')

    # Заполняем команды
    teams_data = [
        ('Man City', 'Manchester', 'Etihad'),
        ('Chelsea', 'London', 'Stamford Bridge'),
        ('Aston Villa', 'Birmingham', 'Villa Park'),
        ('Liverpool', 'Liverpool', 'Anfield'),
        ('Tottenham', 'London', 'Tottenham Hotspur Stadium'),
        ('Arsenal', 'London', 'Emirates'),
        ('Man United', 'Manchester', 'Old Trafford'),
        ('Newcastle', 'Newcastle', 'St James Park'),
    ]
    cursor.executemany('INSERT INTO teams (team_name, city, stadium) VALUES (?, ?, ?)', teams_data)

    # Получаем словарь team_id для быстрого доступа
    cursor.execute('SELECT team_name, team_id FROM teams')
    team_ids = {row[0]: row[1] for row in cursor.fetchall()}

    # Заполняем игроков и статистику
    players_stats_data = [
        ('Erling Haaland', 'Man City', 'FW', 24, 27, 5, 31, 24.5, 6.2),
        ('Cole Palmer', 'Chelsea', 'MF', 22, 22, 11, 34, 18.2, 12.5),
        ('Ollie Watkins', 'Aston Villa', 'FW', 28, 19, 13, 37, 17.8, 11.8),
        ('Mohamed Salah', 'Liverpool', 'FW', 32, 18, 9, 32, 15.2, 10.2),
        ('Son Heung-min', 'Tottenham', 'FW', 31, 17, 10, 35, 14.8, 9.5),
        ('Bukayo Saka', 'Arsenal', 'MF', 22, 16, 9, 35, 13.5, 10.5),
        ('Phil Foden', 'Man City', 'MF', 23, 19, 8, 35, 14.2, 9.2),
        ('Bruno Fernandes', 'Man United', 'MF', 29, 10, 8, 35, 7.2, 9.5),
        ('Alexander Isak', 'Newcastle', 'FW', 24, 21, 2, 30, 16.5, 3.5),
    ]

    for player in players_stats_data:
        name, team_name, pos, age, goals, assists, matches, xg, xa = player
        team_id = team_ids.get(team_name)
        if team_id:
            # Вставляем игрока
            cursor.execute('''
                INSERT INTO players (player_name, team_id, position, age)
                VALUES (?, ?, ?, ?)
            ''', (name, team_id, pos, age))
            player_id = cursor.lastrowid

            # Вставляем статистику
            cursor.execute('''
                INSERT INTO player_stats (player_id, season, goals, assists, matches, xg, xa)
                VALUES (?, '2023/2024', ?, ?, ?, ?, ?)
            ''', (player_id, goals, assists, matches, xg, xa))

    conn.commit()
    conn.close()
    print("✅ База данных 'football_stats.db' успешно создана и заполнена данными!")
    print("   Таблицы: teams, players, player_stats")


if __name__ == "__main__":
    setup_sqlite_db()