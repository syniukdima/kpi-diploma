import mysql.connector
import json
import os
import numpy as np
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
            database=os.getenv('DB_NAME', 'diploma'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        self.cursor = self.connection.cursor(dictionary=True)

    def save_raw_data(self, service_name, metric_type, date, time, values):
        """
        Зберігає сирі дані в таблицю raw_metrics
        
        Args:
            service_name (str): Назва мікросервісу
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date (str): Дата у форматі 'YYYY-MM-DD'
            time (str): Час у форматі 'HH:MM:SS'
            values (list): Список значень метрики
            
        Returns:
            bool: True, якщо дані успішно збережено, False - інакше
        """
        try:
            query = """
            INSERT INTO raw_metrics (service_name, metric_type, date, time, value)
            VALUES (%s, %s, %s, %s, %s)
            """
            values_json = json.dumps(values)
            self.cursor.execute(query, (service_name, metric_type, date, time, values_json))
            self.connection.commit()
            print(f"Дані успішно збережено в raw_metrics")
            return True
        except Exception as e:
            self.connection.rollback()
            print(f"Помилка при збереженні даних в raw_metrics: {e}")
            return False

    def normalize_data(self, values, method="standard"):
        """
        Нормалізація даних
        
        Args:
            values (list): Список значень для нормалізації
            method (str): Метод нормалізації ('standard', 'minmax', 'robust')
            
        Returns:
            list: Нормалізовані значення
        """
        values = np.array(values)
        
        if method == "standard":
            # Стандартна нормалізація (z-score)
            mean = np.mean(values)
            std = np.std(values)
            if std == 0:
                return values.tolist()
            return ((values - mean) / std).tolist()
        
        elif method == "minmax":
            # Min-Max нормалізація
            min_val = np.min(values)
            max_val = np.max(values)
            if max_val == min_val:
                return np.zeros_like(values).tolist()
            return ((values - min_val) / (max_val - min_val)).tolist()
        
        elif method == "robust":
            # Робастна нормалізація (використовує медіану та IQR)
            median = np.median(values)
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            if iqr == 0:
                return values.tolist()
            return ((values - median) / iqr).tolist()
        
        else:
            # За замовчуванням - без нормалізації
            return values.tolist()

    def save_processed_data(self, service_name, metric_type, date, time, processed_values, normalization_type="standard"):
        """
        Зберігає оброблені дані в таблицю processed_metrics
        
        Args:
            service_name (str): Назва мікросервісу
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date (str): Дата у форматі 'YYYY-MM-DD'
            time (str): Час у форматі 'HH:MM:SS'
            processed_values (list): Список вже оброблених значень метрики
            normalization_type (str): Тип нормалізації
            
        Returns:
            bool: True, якщо дані успішно збережено, False - інакше
        """
        try:
            query = """
            INSERT INTO processed_metrics 
            (service_name, metric_type, date, time, value, normalization_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            values_json = json.dumps(processed_values)
            self.cursor.execute(query, (
                service_name, metric_type, date, time, 
                values_json, normalization_type
            ))
            self.connection.commit()
            print(f"Дані успішно збережено в processed_metrics")
            return True
        except Exception as e:
            self.connection.rollback()
            print(f"Помилка при збереженні даних в processed_metrics: {e}")
            return False

    def process_and_save_data(self, service_name, metric_type, date, time, raw_values, normalization_type="standard"):
        """
        Обробляє та зберігає дані в обидві таблиці: raw_metrics та processed_metrics
        
        Args:
            service_name (str): Назва мікросервісу
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date (str): Дата у форматі 'YYYY-MM-DD'
            time (str): Час у форматі 'HH:MM:SS'
            raw_values (list): Список сирих значень метрики
            normalization_type (str): Тип нормалізації
            
        Returns:
            tuple: (raw_success, processed_success) - результати збереження в обидві таблиці
        """
        # Зберігаємо сирі дані
        raw_success = self.save_raw_data(service_name, metric_type, date, time, raw_values)
        
        # Нормалізуємо дані
        processed_values = self.normalize_data(raw_values, method=normalization_type)
        
        # Зберігаємо оброблені дані
        processed_success = self.save_processed_data(
            service_name, metric_type, date, time, processed_values, normalization_type
        )
        
        return raw_success, processed_success

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

    def batch_save_raw_data(self, data_list):
        """
        Пакетне збереження сирих даних в таблицю raw_metrics
        
        Args:
            data_list: Список кортежів (service_name, metric_type, date, time, values)
            
        Returns:
            int: Кількість успішно збережених записів
        """
        success_count = 0
        for data in data_list:
            service_name, metric_type, date, time, values = data
            if self.save_raw_data(service_name, metric_type, date, time, values):
                success_count += 1
        
        return success_count

    def batch_save_processed_data(self, data_list):
        """
        Пакетне збереження оброблених даних в таблицю processed_metrics
        
        Args:
            data_list: Список кортежів (service_name, metric_type, date, time, processed_values, normalization_type)
            
        Returns:
            int: Кількість успішно збережених записів
        """
        success_count = 0
        for data in data_list:
            if len(data) == 5:
                service_name, metric_type, date, time, processed_values = data
                normalization_type = "standard"
            else:
                service_name, metric_type, date, time, processed_values, normalization_type = data
                
            if self.save_processed_data(service_name, metric_type, date, time, processed_values, normalization_type):
                success_count += 1
        
        return success_count

    def normalize_to_percentage(self, values, metric_type, max_ram_kb=2097152, max_channel_kb=None):
        """
        Нормалізує дані в межах 0-100 (відсотки)
        
        Args:
            values (list): Список значень для нормалізації
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            max_ram_kb (int, optional): Максимальне значення RAM в КБ. За замовчуванням 2097152 КБ (2 ГБ)
            max_channel_kb (float, optional): Максимальне значення мережевого трафіку в КБ/с.
                                            Якщо None, буде використано максимальне значення з даних
                                            
        Returns:
            list: Нормалізовані значення у відсотках (0-100), заокруглені до двох знаків після коми
        """
        values = np.array(values)
        
        if metric_type == "CPU":
            # CPU вже у відсотках, просто обмежуємо діапазон 0-100
            normalized = np.clip(values, 0, 100)
        
        elif metric_type == "RAM":
            # Нормалізація RAM відносно максимального значення
            if max_ram_kb <= 0:
                raise ValueError("max_ram_kb повинен бути більше 0")
            
            normalized = (values / max_ram_kb) * 100
            normalized = np.clip(normalized, 0, 100)
        
        elif metric_type == "CHANNEL":
            # Для CHANNEL використовуємо максимальне значення з вибірки
            max_value = np.max(values)
            if max_value > 0:
                # Лінійне масштабування відносно максимального значення
                normalized = (values / max_value) * 100
            else:
                # Якщо всі значення нульові
                normalized = np.zeros_like(values)
            
            normalized = np.clip(normalized, 0, 100)
        
        else:
            raise ValueError(f"Непідтримуваний тип метрики: {metric_type}")
        
        # Заокруглення до двох знаків після коми
        normalized = np.round(normalized, 2)
        
        return normalized.tolist()

    def process_and_save_percentage_data(self, service_name, metric_type, date, time, raw_values, 
                                       max_ram_kb=2097152, max_channel_kb=None):
        """
        Обробляє дані, нормалізує їх у відсотки (0-100) та зберігає в таблицю processed_metrics
        
        Args:
            service_name (str): Назва мікросервісу
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date (str): Дата у форматі 'YYYY-MM-DD'
            time (str): Час у форматі 'HH:MM:SS'
            raw_values (list): Список сирих значень метрики
            max_ram_kb (int, optional): Максимальне значення RAM в КБ
            max_channel_kb (float, optional): Максимальне значення мережевого трафіку в КБ/с
            
        Returns:
            bool: True, якщо дані успішно збережено, False - інакше
        """
        try:
            # Нормалізуємо дані у відсотки
            percentage_values = self.normalize_to_percentage(
                raw_values, metric_type, max_ram_kb, max_channel_kb
            )
            
            # Зберігаємо оброблені дані
            return self.save_processed_data(
                service_name, metric_type, date, time, percentage_values, "percentage"
            )
            
        except Exception as e:
            print(f"Помилка при обробці та збереженні даних у відсотках: {e}")
            return False

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
    
    # Створення об'єкта DBOutput
    db_output = DBOutput()
    
    # Приклад збереження сирих даних
    db_output.save_raw_data("test_service", "CPU", "2023-01-01", "12:00:00", [10, 20, 30, 40, 50])
    
    # Приклад збереження оброблених даних
    processed_values = db_output.normalize_data([10, 20, 30, 40, 50])
    db_output.save_processed_data("test_service", "CPU", "2023-01-01", "12:00:00", processed_values)
    
    # Приклад обробки та збереження даних в обидві таблиці
    db_output.process_and_save_data("test_service", "RAM", "2023-01-01", "12:00:00", [15, 25, 35, 45, 55])
    
    # Закриття з'єднання
    db_output.close() 