import pandas as pd
import json
import os
import re
import sys
from datetime import datetime

# Додаємо батьківську директорію до шляху для імпорту модулів
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(script_dir))
from shared.db_output import DBOutput

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

# Обробка кожного файлу
for filename in files:
    try:
        # Зчитуємо дані з CSV файлу
        df = pd.read_csv(os.path.join(folder, filename))
        
        # Отримуємо назву сервісу з імені файлу
        service_name = f"service_{filename.split('.')[0]}"
        
        # Беремо перший timestamp з даних для цього часового ряду
        first_timestamp_ms = df['Timestamp [ms]'].iloc[0]
        # Конвертуємо з мілісекунд в секунди і створюємо об'єкт datetime
        timestamp_datetime = datetime.fromtimestamp(first_timestamp_ms / 1000)
        # Форматуємо дату і час
        date_str = timestamp_datetime.strftime('%Y-%m-%d')
        time_str = timestamp_datetime.strftime('%H:%M:00')  # Округляємо до хвилин
        
        # Отримуємо значення для кожної метрики
        cpu_values = df['CPU usage [MHZ]'].tolist()[:group_size]  # MHz
        ram_values = df['Memory usage [KB]'].tolist()[:group_size]  # KB
        channel_values = df['Network transmitted throughput [KB/s]'].tolist()[:group_size]  # KB/s
        
        # Зберігаємо сирі дані
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
            
        # Зберігаємо нормалізовані дані (у відсотках відносно стандартної конфігурації)
        cpu_processed_saved = db_output.process_and_save_percentage_data(
            service_name, "CPU", date_str, time_str, cpu_values
        )
        ram_processed_saved = db_output.process_and_save_percentage_data(
            service_name, "RAM", date_str, time_str, ram_values
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
        print(f"Дата: {date_str}, Час: {time_str}")
        print(f"Збережено метрик: {saved_raw_metrics} сирих, {saved_processed_metrics} оброблених")
        
    except Exception as e:
        print(f"Помилка при обробці файлу {filename}: {str(e)}")

print("\nОбробка завершена!")
print(f"Оброблено файлів: {processed_files}/{total_files}")
print(f"Збережено метрик: {saved_raw_metrics} сирих, {saved_processed_metrics} оброблених")
