from fbref2pandas.classes import MatchLogsLink, Data
import pandas as pd

# ------------------------------------------------------------------
# ПАРАМЕТРЫ ДЛЯ СБОРА ДАННЫХ АПЛ 2025/26
# ------------------------------------------------------------------

# 1. team_id - идентификатор команды (8 символов)
# Берем любую команду АПЛ, так как данные возвращаются по всей лиге
TEAM_ID = "b8c2d6b0"  # ID АПЛ на FBref
# Альтернативные ID команд: '822bd0ba' (Man City), '18bb7c10' (Liverpool)

# 2. Сезон
YEAR = "2025-2026"

# 3. comp_id - ID соревнования
# 'c9' = Premier League (АПЛ)
COMP_ID = "c9"

# 4. Типы статистики, которые мы собираем
LOG_TYPES = [
    'scores_and_fixtures',  # Общая статистика (голы, матчи, минуты)
    'shooting',             # Удары, xG
    'passing',              # Пасы
    'defensive_actions',    # Отборы, перехваты
    'possession',           # Владение (для команд)
    'miscellaneous_stats'   # Желтые карточки, фолы и т.д.
]

# ------------------------------------------------------------------
# СБОР ДАННЫХ
# ------------------------------------------------------------------

def collect_all_data():
    """Собирает все типы статистики для АПЛ"""
    
    all_data = {}
    
    for log_type in LOG_TYPES:
        print(f"📥 Сбор данных: {log_type}...")
        
        try:
            # Создаем объект ссылки
            link = MatchLogsLink(TEAM_ID, YEAR, COMP_ID, log_type)
            
            # Получаем данные
            data = Data(link)
            df = data.fbref2pandas()
            
            all_data[log_type] = df
            print(f"   ✅ Загружено {len(df)} записей")
            
        except Exception as e:
            print(f"   ❌ Ошибка при сборе {log_type}: {e}")
    
    return all_data

def create_main_players_table(all_data):
    """Создает основную таблицу игроков из собранных данных"""
    
    # Основная статистика (голы, матчи, минуты, позиции)
    main_stats = all_data.get('scores_and_fixtures')
    
    if main_stats is None:
        print("❌ Не удалось получить основную статистику")
        return None
    
    # Очистка данных
    main_stats = main_stats.dropna(subset=['Player'])
    main_stats = main_stats[main_stats['Player'] != 'Player']
    
    # Выбираем нужные колонки
    columns_needed = ['Player', 'Nation', 'Pos', 'Age', 'MP', 'Starts', 'Min', 'Gls', 'Ast']
    available_cols = [col for col in columns_needed if col in main_stats.columns]
    players_df = main_stats[available_cols].copy()
    
    # Добавляем xG из таблицы shooting
    if 'shooting' in all_data:
        shooting = all_data['shooting']
        if 'Player' in shooting.columns and 'xG' in shooting.columns:
            xg_data = shooting[['Player', 'xG']].dropna(subset=['xG'])
            players_df = players_df.merge(xg_data, on='Player', how='left')
    
    # Добавляем xA из таблицы passing
    if 'passing' in all_data:
        passing = all_data['passing']
        if 'Player' in passing.columns and 'xA' in passing.columns:
            xa_data = passing[['Player', 'xA']].dropna(subset=['xA'])
            players_df = players_df.merge(xa_data, on='Player', how='left')
    
    # Переименовываем колонки
    players_df = players_df.rename(columns={
        'Player': 'player_name',
        'Nation': 'nationality',
        'Pos': 'position',
        'Age': 'age',
        'MP': 'matches',
        'Starts': 'starts',
        'Min': 'minutes_played',
        'Gls': 'goals',
        'Ast': 'assists'
    })
    
    # Конвертируем числовые колонки
    numeric_cols = ['age', 'matches', 'starts', 'minutes_played', 'goals', 'assists', 'xG', 'xA']
    for col in numeric_cols:
        if col in players_df.columns:
            players_df[col] = pd.to_numeric(players_df[col], errors='coerce')
    
    # Рассчитываем метрики на 90 минут
    players_df['goals_per_90'] = players_df.apply(
        lambda x: x['goals'] * 90 / x['minutes_played'] if x['minutes_played'] > 0 else 0, axis=1
    )
    players_df['assists_per_90'] = players_df.apply(
        lambda x: x['assists'] * 90 / x['minutes_played'] if x['minutes_played'] > 0 else 0, axis=1
    )
    
    return players_df

def create_teams_table(all_data):
    """Создает таблицу команд из собранных данных"""
    
    # Командная статистика доступна в таблице possession
    possession = all_data.get('possession')
    
    if possession is None:
        print("⚠️ Данные команд не получены")
        return None
    
    # Выбираем строки с командами (не игроками)
    # Обычно в таблице possession есть строки с суммами по командам
    teams_data = possession[possession['Player'].str.contains('Team', na=False, case=False)] if 'Player' in possession.columns else None
    
    if teams_data is None or len(teams_data) == 0:
        # Альтернативный способ: создаем простую таблицу команд
        teams_data = pd.DataFrame({
            'team_name': ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton',
                         'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Ipswich Town',
                         'Leicester City', 'Liverpool', 'Man City', 'Man United', 'Newcastle',
                         'Nottingham Forest', 'Southampton', 'Tottenham', 'West Ham', 'Wolves'],
            'matches': [0] * 20,
            'points': [0] * 20
        })
    
    return teams_data

# ------------------------------------------------------------------
# СОХРАНЕНИЕ В БАЗУ ДАННЫХ
# ------------------------------------------------------------------

def save_to_sqlite(players_df, teams_df):
    """Сохраняет данные в SQLite базу данных"""
    
    import sqlite3
    
    conn = sqlite3.connect('football_stats.db')
    
    # Сохраняем таблицы
    players_df.to_sql('players_data', conn, if_exists='replace', index=False)
    
    if teams_df is not None:
        teams_df.to_sql('teams_data', conn, if_exists='replace', index=False)
    
    conn.close()
    print("✅ Данные сохранены в football_stats.db")

# ------------------------------------------------------------------
# ЗАПУСК
# ------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("🏆 СБОР СТАТИСТИКИ АПЛ 2025/26")
    print("=" * 50)
    print()
    
    # Сбор данных
    all_data = collect_all_data()
    print()
    
    # Создание таблиц
    players_df = create_main_players_table(all_data)
    teams_df = create_teams_table(all_data)
    
    if players_df is not None:
        print(f"\n📊 Таблица игроков: {len(players_df)} записей")
        print(players_df.head())
    else:
        print("❌ Таблица игроков не создана")
    
    # Сохранение
    if players_df is not None:
        save_to_sqlite(players_df, teams_df)
    
    print("\n✨ Готово!")