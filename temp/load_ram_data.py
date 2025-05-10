import json
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, time

# Завантаження змінних середовища з .env файлу
load_dotenv()

def load_ram_data():
    """
    Завантажує дані з файлу microservices_data.json у базу даних
    як оброблені дані RAM для дати 2015-10-05 та часу 19:00
    """
    # Підключення до бази даних
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'root'),
        database=os.getenv('DB_NAME', 'diploma')
    )
    cursor = connection.cursor()
    
    try:
        # Завантаження даних з файлу
        with open('microservices_data.json', 'r') as file:
            microservices_data = json.load(file)
        
        print(f"Завантажено дані для {len(microservices_data)} мікросервісів")
        
        # Визначення назв мікросервісів
        service_names = [f"service_{i+1}" for i in range(len(microservices_data))]
        
        # Дата та час для вставки
        target_date = '2015-10-05'
        target_time = '19:00:00'
        
        # Підготовка та вставка даних
        records_count = 0
        
        for i, (service_data, service_name) in enumerate(zip(microservices_data, service_names)):
            # Перетворення списку значень у JSON
            value_json = json.dumps(service_data)
            
            # Вставка запису
            query = """
            INSERT INTO processed_metrics 
            (service_name, metric_type, date, time, value, normalization_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE value = %s
            """
            cursor.execute(query, (
                service_name,
                'RAM',
                target_date,
                target_time,
                value_json,
                'standard',
                value_json
            ))
            records_count += 1
        
        # Зберігаємо зміни
        connection.commit()
        print(f"Додано {records_count} записів у таблицю processed_metrics")
        
    except Exception as e:
        connection.rollback()
        print(f"Помилка при завантаженні даних: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    load_ram_data() 