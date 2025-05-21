import mysql.connector
import json
import os
from dotenv import load_dotenv

# Завантаження змінних середовища з .env файлу
load_dotenv()

class DBInput:
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

    def get_data_for_algorithm(self, metric_type, date=None, time=None, normalization_type=None):
        """
        Отримання даних у форматі, готовому для алгоритму групування
        
        Args:
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date (str, optional): Дата у форматі 'YYYY-MM-DD'
            time (str, optional): Час у форматі 'HH:MM:SS'
            normalization_type (str, optional): Тип нормалізації (якщо None, не фільтрує за типом)
            
        Returns:
            tuple: (microservices, service_names)
                microservices - список списків значень для кожного мікросервісу
                service_names - список назв мікросервісів
        """
        query = """
        SELECT service_name, value 
        FROM processed_metrics 
        WHERE metric_type = %s
        """
        params = [metric_type]
        
        if normalization_type:
            query += " AND normalization_type = %s"
            params.append(normalization_type)
        
        if date:
            query += " AND date = %s"
            params.append(date)
        
        if time:
            query += " AND time = %s"
            params.append(time)
        
        query += " ORDER BY service_name"
        
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        
        microservices = []
        service_names = []
        
        for row in results:
            service_names.append(row['service_name'])
            values = json.loads(row['value'])
            microservices.append(values)
        
        return microservices, service_names

    def close(self):
        """
        Закриття з'єднання з базою даних
        """
        self.cursor.close()
        self.connection.close()

# Приклад використання:
if __name__ == "__main__":
    db_input = DBInput()
    
    # Отримання даних для алгоритму (приклад)
    microservices, service_names = db_input.get_data_for_algorithm('CPU', '2015-05-10', '19:00:00')
    print(f"Отримано дані для {len(microservices)} мікросервісів")
    print(f"Назви мікросервісів: {service_names}")
    if microservices:
        print(f"Приклад даних: {microservices[0]}")
    
    db_input.close() 