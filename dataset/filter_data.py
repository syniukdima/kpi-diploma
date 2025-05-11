import pandas as pd
import json
import os
import re
import sys
from datetime import datetime

# Додаємо батьківську директорію до шляху для імпорту модулів
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(script_dir))
from db_output import DBOutput

# Папка з файлами (використовуємо абсолютний шлях)
folder = script_dir
group_size = 24

# Максимальні значення для нормалізації
MAX_RAM_KB = 2097152  # 2 ГБ в КБ

# Створюємо об'єкт для роботи з базою даних
db_output = DBOutput()

# Отримати всі файли з назвами типу "5.csv", "10.csv", ...
files = [f for f in os.listdir(folder) if re.match(r'^\d+\.csv$', f)]

# Лічильники для статистики
total_files = len(files)
processed_files = 0
saved_raw_metrics = 0
saved_processed_metrics = 0

print(f"Знайдено {total_files} файлів для обробки")

for filename in files:
    filepath = os.path.join(folder, filename)
    service_id = os.path.splitext(filename)[0]  # число з назви
    service_name = f'dataset_service_{service_id}'

    try:
        # Завантаження та підготовка
        df = pd.read_csv(filepath)

        # Вибір і перейменування
        df = df[['Timestamp [ms]', 'CPU usage [%]', 'Memory usage [KB]', 'Network transmitted throughput [KB/s]']]
        df.columns = ['TimeStamp', 'cpu_load %', 'memory_usage [KB]', 'throughput [KB/s]']

        # Час і очищення
        df['TimeStamp'] = pd.to_datetime(df['TimeStamp'], unit='s')
        df.replace(0, pd.NA, inplace=True)
        df = df.fillna(method='bfill').fillna(method='ffill')

        # Округлення
        df['cpu_load %'] = df['cpu_load %'].round(2)
        df['memory_usage [KB]'] = df['memory_usage [KB]'].round(2)
        df['throughput [KB/s]'] = df['throughput [KB/s]'].round(2)

        # Перша повна група з 24 рядків
        if len(df) < group_size:
            print(f"Пропускаємо файл {filename}: недостатньо даних")
            continue  # Пропускаємо якщо даних недостатньо

        chunk = df.iloc[:group_size]
        timestamp = chunk.iloc[0]['TimeStamp']
        
        # Заокруглення часу до годин і хвилин (без секунд)
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:00')  # Заокруглюємо секунди до 00
        
        cpu_values = chunk['cpu_load %'].tolist()
        ram_values = chunk['memory_usage [KB]'].tolist()
        channel_values = chunk['throughput [KB/s]'].tolist()

        # Зберігаємо сирі дані в базу даних
        cpu_raw_saved = db_output.save_raw_data(service_name, "CPU", date_str, time_str, cpu_values)
        ram_raw_saved = db_output.save_raw_data(service_name, "RAM", date_str, time_str, ram_values)
        channel_raw_saved = db_output.save_raw_data(service_name, "CHANNEL", date_str, time_str, channel_values)
        
        # Підраховуємо кількість збережених сирих метрик
        if cpu_raw_saved:
            saved_raw_metrics += 1
        if ram_raw_saved:
            saved_raw_metrics += 1
        if channel_raw_saved:
            saved_raw_metrics += 1
            
        # Зберігаємо нормалізовані дані (у відсотках)
        # Для CHANNEL використовуємо автоматичне визначення максимуму (None)
        cpu_processed_saved = db_output.process_and_save_percentage_data(
            service_name, "CPU", date_str, time_str, cpu_values
        )
        ram_processed_saved = db_output.process_and_save_percentage_data(
            service_name, "RAM", date_str, time_str, ram_values, MAX_RAM_KB
        )
        channel_processed_saved = db_output.process_and_save_percentage_data(
            service_name, "CHANNEL", date_str, time_str, channel_values
        )
        
        # Підраховуємо кількість збережених оброблених метрик
        if cpu_processed_saved:
            saved_processed_metrics += 1
        if ram_processed_saved:
            saved_processed_metrics += 1
        if channel_processed_saved:
            saved_processed_metrics += 1
            
        processed_files += 1
        print(f"Оброблено файл {filename} ({processed_files}/{total_files})")
        
    except Exception as e:
        print(f"Помилка при обробці файлу {filename}: {e}")

# Закриваємо з'єднання з базою даних
db_output.close()

print(f"\nРезультати:")
print(f"Оброблено файлів: {processed_files} з {total_files}")
print(f"Збережено сирих метрик: {saved_raw_metrics}")
print(f"Збережено нормалізованих метрик: {saved_processed_metrics}")
