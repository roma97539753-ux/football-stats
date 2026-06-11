import sqlite3
import pandas as pd

def setup_database():
    conn = sqlite3.connect('football_stats.db')
    cursor = conn.cursor()
    
    # Таблицы
    cursor.execute('DROP TABLE IF EXISTS player_stats')
    cursor.execute('DROP TABLE IF EXISTS players')
    cursor.execute('DROP TABLE IF EXISTS teams')
    
    cursor.execute('''
        CREATE TABLE teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT UNIQUE NOT NULL,
            city TEXT,
            stadium TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE players (
            player_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            team_id INTEGER,
            position TEXT,
            age INTEGER,
            nationality TEXT,
            market_value_million REAL,
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE player_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            season TEXT,
            goals INTEGER,
            assists INTEGER,
            matches INTEGER,
            minutes_played INTEGER,
            xg REAL,
            xa REAL,
            passes_completed INTEGER,
            tackles INTEGER,
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )
    ''')
    
    # Команды
    teams_data = [
        ('Man City', 'Manchester', 'Etihad'),
        ('Arsenal', 'London', 'Emirates'),
        ('Liverpool', 'Liverpool', 'Anfield'),
        ('Aston Villa', 'Birmingham', 'Villa Park'),
        ('Tottenham', 'London', 'Tottenham Hotspur Stadium'),
        ('Chelsea', 'London', 'Stamford Bridge'),
        ('Newcastle', 'Newcastle', 'St James Park'),
        ('Man United', 'Manchester', 'Old Trafford'),
        ('Brighton', 'Brighton', 'Amex'),
        ('West Ham', 'London', 'London Stadium'),
    ]
    cursor.executemany('INSERT INTO teams (team_name, city, stadium) VALUES (?, ?, ?)', teams_data)
    
    # Получаем team_id
    cursor.execute('SELECT team_name, team_id FROM teams')
    team_ids = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Игроки и статистика (50+)
    players_data = [
        ('Erling Haaland', 'Man City', 'FW', 24, 'Norway', 180.0, 27, 5, 31, 2480, 24.5, 6.2, 320, 15),
        ('Phil Foden', 'Man City', 'MF', 23, 'England', 110.0, 19, 8, 35, 2890, 14.2, 9.2, 1850, 45),
        ('Kevin De Bruyne', 'Man City', 'MF', 32, 'Belgium', 70.0, 4, 10, 18, 1350, 3.5, 12.5, 890, 20),
        ('Rodri', 'Man City', 'MF', 27, 'Spain', 100.0, 8, 9, 34, 3010, 5.2, 8.5, 2650, 68),
        ('Bukayo Saka', 'Arsenal', 'MF', 22, 'England', 120.0, 16, 9, 35, 2980, 13.5, 10.5, 1680, 52),
        ('Martin Odegaard', 'Arsenal', 'MF', 25, 'Norway', 90.0, 8, 10, 35, 3050, 6.5, 11.5, 2450, 48),
        ('Declan Rice', 'Arsenal', 'MF', 25, 'England', 110.0, 7, 8, 38, 3420, 4.5, 7.5, 2780, 85),
        ('Mohamed Salah', 'Liverpool', 'FW', 32, 'Egypt', 65.0, 18, 9, 32, 2760, 15.2, 10.2, 1020, 38),
        ('Darwin Nunez', 'Liverpool', 'FW', 24, 'Uruguay', 70.0, 11, 8, 36, 2450, 16.5, 7.5, 620, 25),
        ('Virgil van Dijk', 'Liverpool', 'DF', 32, 'Netherlands', 35.0, 2, 2, 36, 3240, 1.8, 0.8, 2450, 65),
        ('Ollie Watkins', 'Aston Villa', 'FW', 28, 'England', 65.0, 19, 13, 37, 3210, 17.8, 11.8, 680, 28),
        ('Son Heung-min', 'Tottenham', 'FW', 31, 'South Korea', 50.0, 17, 10, 35, 3050, 14.8, 9.5, 890, 28),
        ('James Maddison', 'Tottenham', 'MF', 27, 'England', 60.0, 4, 9, 28, 2150, 4.5, 8.5, 1450, 28),
        ('Cole Palmer', 'Chelsea', 'MF', 22, 'England', 80.0, 22, 11, 34, 2980, 18.2, 12.5, 1580, 45),
        ('Nicolas Jackson', 'Chelsea', 'FW', 22, 'Senegal', 40.0, 14, 5, 35, 2670, 16.5, 6.5, 520, 25),
        ('Alexander Isak', 'Newcastle', 'FW', 24, 'Sweden', 70.0, 21, 2, 30, 2350, 16.5, 3.5, 480, 18),
        ('Bruno Guimaraes', 'Newcastle', 'MF', 26, 'Brazil', 85.0, 7, 8, 37, 3150, 5.5, 7.5, 2450, 85),
        ('Bruno Fernandes', 'Man United', 'MF', 29, 'Portugal', 70.0, 10, 8, 35, 3050, 7.2, 9.5, 2650, 58),
        ('Marcus Rashford', 'Man United', 'FW', 26, 'England', 60.0, 7, 5, 33, 2450, 8.5, 6.5, 720, 22),
        ('Joao Pedro', 'Brighton', 'FW', 22, 'Brazil', 32.0, 9, 3, 31, 2350, 10.5, 4.5, 520, 22),
        ('Kaoru Mitoma', 'Brighton', 'MF', 26, 'Japan', 45.0, 7, 6, 34, 2670, 6.5, 7.5, 980, 32),
        ('Jarrod Bowen', 'West Ham', 'FW', 27, 'England', 50.0, 16, 6, 34, 2980, 12.5, 7.5, 680, 32),
        ('Mohammed Kudus', 'West Ham', 'MF', 23, 'Ghana', 45.0, 8, 6, 33, 2450, 7.5, 6.5, 850, 38),
    ]
    
    for p in players_data:
        name, team_name, pos, age, nat, mv, goals, assists, matches, minutes, xg, xa, passes, tackles = p
        team_id = team_ids.get(team_name)
        if team_id:
            cursor.execute('''
                INSERT INTO players (player_name, team_id, position, age, nationality, market_value_million)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, team_id, pos, age, nat, mv))
            player_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO player_stats (player_id, season, goals, assists, matches, minutes_played, xg, xa, passes_completed, tackles)
                VALUES (?, '2023/2024', ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (player_id, goals, assists, matches, minutes, xg, xa, passes, tackles))
    
    conn.commit()
    conn.close()
    print("✅ База данных football_stats.db создана!")
    print(f"   Команд: {len(teams_data)}")
    print(f"   Игроков: {len(players_data)}")

if __name__ == "__main__":
    setup_database()