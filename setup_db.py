import psycopg2
from sqlalchemy import create_engine
import pandas as pd

# ⚠️ ЗАМЕНИТЕ ЭТУ СТРОКУ на вашу из Supabase
DATABASE_URL = "postgresql://postgres.venyuobqorgjakbbyxax:Romafedorov2100@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"


def create_tables():
    """Создает 3 таблицы: teams, players, player_stats"""

    engine = create_engine(DATABASE_URL)

    # SQL для создания таблиц
    create_teams_table = """
    CREATE TABLE IF NOT EXISTS teams (
        team_id SERIAL PRIMARY KEY,
        team_name VARCHAR(100) UNIQUE NOT NULL,
        city VARCHAR(100),
        stadium VARCHAR(100)
    );
    """

    create_players_table = """
    CREATE TABLE IF NOT EXISTS players (
        player_id SERIAL PRIMARY KEY,
        player_name VARCHAR(100) NOT NULL,
        team_id INTEGER REFERENCES teams(team_id),
        position VARCHAR(10),
        age INTEGER
    );
    """

    create_stats_table = """
    CREATE TABLE IF NOT EXISTS player_stats (
        stat_id SERIAL PRIMARY KEY,
        player_id INTEGER REFERENCES players(player_id),
        season VARCHAR(20),
        goals INTEGER DEFAULT 0,
        assists INTEGER DEFAULT 0,
        matches INTEGER DEFAULT 0,
        xg FLOAT DEFAULT 0,
        xa FLOAT DEFAULT 0
    );
    """

    with engine.connect() as conn:
        conn.execute(create_teams_table)
        conn.execute(create_players_table)
        conn.execute(create_stats_table)
        conn.commit()

    print("✅ Таблицы созданы: teams, players, player_stats")


def insert_demo_data():
    """Заполняет таблицы демо-данными"""

    engine = create_engine(DATABASE_URL)

    # Данные команд
    teams_data = [
        ('Man City', 'Manchester', 'Etihad'),
        ('Chelsea', 'London', 'Stamford Bridge'),
        ('Aston Villa', 'Birmingham', 'Villa Park'),
        ('Liverpool', 'Liverpool', 'Anfield'),
        ('Tottenham', 'London', 'Tottenham Hotspur'),
        ('Arsenal', 'London', 'Emirates'),
        ('Man United', 'Manchester', 'Old Trafford'),
        ('Newcastle', 'Newcastle', 'St James Park'),
    ]

    # Данные игроков + статистика
    players_stats = [
        ('Erling Haaland', 'Man City', 'FW', 24, 27, 5, 31, 24.5, 6.2),
        ('Cole Palmer', 'Chelsea', 'MF', 22, 22, 11, 34, 18.2, 12.5),
        ('Ollie Watkins', 'Aston Villa', 'FW', 28, 19, 13, 37, 17.8, 11.8),
        ('Mohamed Salah', 'Liverpool', 'FW', 31, 18, 9, 32, 15.2, 10.2),
        ('Son Heung-min', 'Tottenham', 'FW', 31, 17, 10, 35, 14.8, 9.5),
        ('Bukayo Saka', 'Arsenal', 'MF', 22, 16, 9, 35, 13.5, 10.5),
        ('Phil Foden', 'Man City', 'MF', 23, 19, 8, 35, 14.2, 9.2),
        ('Bruno Fernandes', 'Man United', 'MF', 29, 10, 8, 35, 7.2, 9.5),
        ('Alexander Isak', 'Newcastle', 'FW', 24, 21, 2, 30, 16.5, 3.5),

    ]

    with engine.connect() as conn:
        # Вставляем команды
        for team_name, city, stadium in teams_data:
            conn.execute(
                "INSERT INTO teams (team_name, city, stadium) VALUES (%s, %s, %s) ON CONFLICT (team_name) DO NOTHING",
                (team_name, city, stadium)
            )

        # Вставляем игроков и статистику
        for player_name, team_name, pos, age, goals, assists, matches, xg, xa in players_stats:
            # Получаем team_id
            result = conn.execute("SELECT team_id FROM teams WHERE team_name = %s", (team_name,))
            team_id = result.fetchone()[0]

            # Вставляем игрока
            conn.execute(
                "INSERT INTO players (player_name, team_id, position, age) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (player_name, team_id, pos, age)
            )

            # Получаем player_id
            result = conn.execute("SELECT player_id FROM players WHERE player_name = %s", (player_name,))
            player_id = result.fetchone()[0]

            # Вставляем статистику
            conn.execute(
                "INSERT INTO player_stats (player_id, season, goals, assists, matches, xg, xa) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (player_id, '2023/2024', goals, assists, matches, xg, xa)
            )

        conn.commit()

    print("✅ Данные загружены в БД")


if __name__ == "__main__":
    create_tables()
    insert_demo_data()
    print("\n🎉 База данных готова! Теперь можно запускать дашборд.")