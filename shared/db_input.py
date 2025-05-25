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

    def get_data_for_algorithm(self, metric_type, date=None, time=None):
        """
        Отримання даних у форматі, готовому для алгоритму групування
        
        Args:
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date (str, optional): Дата у форматі 'YYYY-MM-DD'
            time (str, optional): Час у форматі 'HH:MM:SS'
            
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

    def get_raw_data_for_algorithm(self, metric_type, date=None, time=None):
        """
        Отримання сирих даних метрик для нормалізації
        
        Args:
            metric_type (str): Тип метрики ('CPU', 'RAM', 'CHANNEL')
            date (str, optional): Дата у форматі 'YYYY-MM-DD'
            time (str, optional): Час у форматі 'HH:MM:SS'
            
        Returns:
            tuple: (raw_data, service_names)
                raw_data - список списків сирих значень для кожного мікросервісу
                service_names - список назв мікросервісів
        """
        query = """
        SELECT service_name, value 
        FROM raw_metrics 
        WHERE metric_type = %s
        """
        params = [metric_type]
        
        if date:
            query += " AND date = %s"
            params.append(date)
        
        if time:
            query += " AND time = %s"
            params.append(time)
        
        query += " ORDER BY service_name"
        
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        
        raw_data = []
        service_names = []
        
        for row in results:
            service_names.append(row['service_name'])
            values = json.loads(row['value'])
            raw_data.append(values)
        
        return raw_data, service_names

    def get_all_raw_metrics(self, metric_type=None, service_name=None, date=None, time=None):
        """
        Отримати сирі метрики з бази даних з можливістю фільтрації
        """
        try:
            query = "SELECT service_name, metric_type, date, time, value FROM raw_metrics WHERE 1=1"
            params = []

            if metric_type:
                query += " AND metric_type = %s"
                params.append(metric_type)
            
            if service_name:
                query += " AND service_name = %s"
                params.append(service_name)
            
            if date:
                query += " AND date = %s"
                params.append(date)
            
            if time:
                query += " AND time = %s"
                params.append(time)

            query += " ORDER BY date DESC, time DESC"
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            result = []
            for row in rows:
                try:
                    result.append({
                        "service_name": row["service_name"],
                        "metric_type": row["metric_type"],
                        "date": row["date"].strftime("%Y-%m-%d"),
                        "time": row["time"].strftime("%H:%M:%S") if hasattr(row["time"], "strftime") else str(row["time"]),
                        "values": json.loads(row["value"])
                    })
                except Exception as e:
                    continue
            
            return result
            
        except Exception as e:
            print(f"Error in get_all_raw_metrics: {str(e)}")
            return []

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