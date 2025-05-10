import mysql.connector
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Завантаження змінних середовища з .env файлу
load_dotenv()

class DBOutput:
    def __init__(self):
        """
        Ініціалізація з'єднання з базою даних
        """
        self.connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'root'),
            database=os.getenv('DB_NAME', 'diploma')
        )
        self.cursor = self.connection.cursor()

    def save_grouping_results(self, groups, group_services, service_names, metric_type, date, time):
        """
        Зберігає результати групування в базу даних
        
        Args:
            groups: Список груп, де кожна група містить часові ряди мікросервісів
            group_services: Список індексів мікросервісів у кожній групі
            service_names: Список назв мікросервісів
            metric_type: Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date: Дата у форматі 'YYYY-MM-DD'
            time: Час у форматі 'HH:MM:SS'
            
        Returns:
            int: Кількість збережених записів
        """
        # Перевіряємо, чи є результати для збереження
        if not groups or not group_services:
            print("Немає результатів для збереження")
            return 0
        
        try:
            # Підготовка даних для вставки
            records_count = 0
            
            # Для кожної групи
            for group_id, (group, service_indices) in enumerate(zip(groups, group_services), 1):
                # Для кожного мікросервісу в групі
                for idx in service_indices:
                    # Визначаємо реальний індекс та назву мікросервісу
                    if idx >= 1000:  # Базовий компонент
                        real_idx = idx - 1000
                        service_name = service_names[real_idx]
                        component_type = "base"
                    elif idx < 0:  # Піковий компонент
                        real_idx = -idx
                        service_name = service_names[real_idx]
                        component_type = "peak"
                    else:  # Звичайний мікросервіс
                        service_name = service_names[idx]
                        component_type = "original"
                    
                    # Вставка запису в таблицю grouping_results
                    query = """
                    INSERT INTO grouping_results 
                    (group_id, service_name, date, time, metric_type, component_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    self.cursor.execute(query, (
                        group_id, 
                        service_name, 
                        date,
                        time,
                        metric_type,
                        component_type
                    ))
                    records_count += 1
            
            # Зберігаємо зміни
            self.connection.commit()
            print(f"Збережено {records_count} записів у таблицю grouping_results")
            return records_count
            
        except Exception as e:
            self.connection.rollback()
            print(f"Помилка при збереженні результатів: {e}")
            return 0

    def close(self):
        """
        Закриття з'єднання з базою даних
        """
        self.cursor.close()
        self.connection.close()

# Приклад використання:
if __name__ == "__main__":
    from db_input import DBInput
    from group_finder import form_multiple_knapsack_groups
    
    # Отримання даних з бази даних
    db_input = DBInput()
    date = '2015-05-10'
    time = '19:00:00'
    metric_type = 'CPU'
    
    microservices, service_names = db_input.get_data_for_algorithm(metric_type, date, time)
    db_input.close()
    
    print(f"Отримано дані для {len(microservices)} мікросервісів")
    
    # Формування груп
    groups, group_services, slot_sums = form_multiple_knapsack_groups(microservices, max_group_size=4)
    
    # Збереження результатів в базу даних
    db_output = DBOutput()
    db_output.save_grouping_results(groups, group_services, service_names, metric_type, date, time)
    db_output.close() 