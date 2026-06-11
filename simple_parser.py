import pandas as pd
import numpy as np

# URL страницы со статистикой АПЛ 2025/26
# Используем мобильную версию или добавляем параметр, чтобы избежать блокировки
url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"

print("📥 Загрузка данных с FBref...")

try:
    # Читаем все таблицы со страницы
    # header=None и names для корректного парсинга
    tables = pd.read_html(url, header=0)
    
    print(f"✅ Найдено таблиц: {len(tables)}")
    
    # Первая таблица — обычно стандартная статистика игроков
    if len(tables) > 0:
        df_players_raw = tables[0]
        print(f"📊 Таблица игроков: {df_players_raw.shape}")
        
        # Очистка данных — убираем строки с пропущенными значениями в имени игрока
        if 'Player' in df_players_raw.columns:
            df_players_raw = df_players_raw[df_players_raw['Player'].notna()]
            df_players_raw = df_players_raw[df_players_raw['Player'] != 'Player']
            
            # Выбираем нужные колонки
            keep_cols = ['Player', 'Nation', 'Pos', 'Age', 'MP', 'Starts', 'Min', 'Gls', 'Ast']
            available_cols = [col for col in keep_cols if col in df_players_raw.columns]
            df_players = df_players_raw[available_cols].copy()
            
            # Переименовываем для удобства
            df_players = df_players.rename(columns={
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
            
            # Конвертируем числовые поля
            numeric_cols = ['age', 'matches', 'starts', 'minutes_played', 'goals', 'assists']
            for col in numeric_cols:
                if col in df_players.columns:
                    df_players[col] = pd.to_numeric(df_players[col], errors='coerce')
            
            # Очищаем от строк-заглушек (например, "League Total")
            df_players = df_players[df_players['player_name'] != 'League Total']
            
            # Добавляем тестовые xG/xA (так как в простой таблице их нет)
            # В реальности xG берется из других таблиц, но для MVP добавим симулированные данные
            np.random.seed(42)
            df_players['xg'] = df_players['goals'] * np.random.uniform(0.8, 1.2, len(df_players))
            df_players['xa'] = df_players['assists'] * np.random.uniform(0.7, 1.3, len(df_players))
            
            # Рассчитываем метрики на 90 минут
            df_players['goals_per_90'] = df_players.apply(
                lambda x: x['goals'] * 90 / x['minutes_played'] if x['minutes_played'] > 0 else 0, axis=1
            )
            df_players['assists_per_90'] = df_players.apply(
                lambda x: x['assists'] * 90 / x['minutes_played'] if x['minutes_played'] > 0 else 0, axis=1
            )
            df_players['xg_per_90'] = df_players.apply(
                lambda x: x['xg'] * 90 / x['minutes_played'] if x['minutes_played'] > 0 else 0, axis=1
            )
            
            print(f"\n✅ Игроков загружено: {len(df_players)}")
            print(df_players.head())
            
            # Сохраняем в CSV
            df_players.to_csv('players_2025_26.csv', index=False)
            print("\n💾 Данные сохранены в players_2025_26.csv")
            
        else:
            print("❌ Колонка 'Player' не найдена в таблице")
            print("Доступные колонки:", df_players_raw.columns.tolist())
    
    # Поиск таблицы с командами/турнирной таблицей
    for i, table in enumerate(tables):
        if 'team' in str(table.columns).lower() or 'club' in str(table.columns).lower():
            print(f"\n📊 Найдена возможная таблица команд (индекс {i})")
            teams_df = table
            teams_df.to_csv('teams_2025_26.csv', index=False)
            print("💾 Данные команд сохранены в teams_2025_26.csv")
            break
            
except Exception as e:
    print(f"❌ Ошибка: {e}")
    print("\nВозможное решение: установите библиотеку lxml")
    print("  pip install lxml")
    
print("\n✨ Готово!")