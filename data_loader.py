import mysql.connector
from datetime import datetime
import json
import numpy as np

class DataLoader:
    def __init__(self, host="localhost", user="root", password="root", database="diploma"):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor()

    def load_raw_data(self, service_name, metric_type, date, time, values):
        """
        Завантаження сирих даних в таблицю raw_metrics
        
        Args:
            service_name (str): Назва мікросервісу
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date (str): Дата у форматі 'YYYY-MM-DD'
            time (str): Час у форматі 'HH:MM:SS'
            values (list): Список значень метрики
        """
        try:
            query = """
            INSERT INTO raw_metrics (service_name, metric_type, date, time, value)
            VALUES (%s, %s, %s, %s, %s)
            """
            values_json = json.dumps(values)
            self.cursor.execute(query, (service_name, metric_type, date, time, values_json))
            self.connection.commit()
            print(f"Дані успішно завантажено в raw_metrics")
        except Exception as e:
            print(f"Помилка при завантаженні даних: {e}")
            self.connection.rollback()

    def normalize_data(self, values):
        """
        Нормалізація даних (зараз проста нормалізація, можна додати інші методи)
        
        Args:
            values (list): Список значень для нормалізації
            
        Returns:
            list: Нормалізовані значення
        """
        values = np.array(values)
        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            return values.tolist()
        return ((values - mean) / std).tolist()

    def load_processed_data(self, service_name, metric_type, date, time, processed_values, normalization_type="standard"):
        """
        Завантаження оброблених даних в таблицю processed_metrics
        
        Args:
            service_name (str): Назва мікросервісу
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date (str): Дата у форматі 'YYYY-MM-DD'
            time (str): Час у форматі 'HH:MM:SS'
            processed_values (list): Список вже оброблених значень метрики
            normalization_type (str): Тип нормалізації
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
            print(f"Дані успішно завантажено в processed_metrics")
        except Exception as e:
            print(f"Помилка при завантаженні даних: {e}")
            self.connection.rollback()


    def close(self):
        """
        Закриття з'єднання з базою даних
        """
        self.cursor.close()
        self.connection.close()

# Приклад використання:
if __name__ == "__main__":
    loader = DataLoader()

    loader.load_processed_data("service_name", "CPU", "2023-01-01", "12:00:00", [1, 2, 3, 4, 5])

    loader.close()