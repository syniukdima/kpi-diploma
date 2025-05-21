import mysql.connector
import json
import os
from dotenv import load_dotenv

# Завантаження змінних середовища з .env файлу
load_dotenv()

def load_test_data():
    """
    Завантаження тестових даних у таблицю processed_metrics
    """
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'root'),
        database=os.getenv('DB_NAME', 'diploma')
    )
    cursor = connection.cursor()
    
    # Тестові дані
    microservices_data = [
        {"name": "microservice_1", "values": [1, 2, 3, 4, 3, 2]},
        {"name": "microservice_2", "values": [1, 2, 3, 4, 3, 2]},
        {"name": "microservice_3", "values": [2, 1, 1, 2, 3, 4]},
        {"name": "microservice_4", "values": [3, 3, 2, 1, 2, 3]},
        {"name": "microservice_5", "values": [4, 3, 2, 1, 1, 2]},
        {"name": "microservice_6", "values": [2, 3, 4, 3, 2, 1]},
        {"name": "microservice_7", "values": [1, 2, 3, 4, 4, 3]},
        {"name": "microservice_8", "values": [3, 2, 1, 2, 3, 4]},
        {"name": "microservice_9", "values": [4, 3, 2, 1, 2, 3]}
    ]
    
    date = "2015-05-10"
    time = "18:00:00"
    metric_type = "CPU"
    normalization_type = "standard"
    
    # Додавання даних у таблицю
    for service in microservices_data:
        query = """
        INSERT INTO processed_metrics 
        (service_name, metric_type, date, time, value, normalization_type)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values_json = json.dumps(service["values"])
        cursor.execute(query, (
            service["name"], 
            metric_type, 
            date, 
            time, 
            values_json, 
            normalization_type
        ))
    
    connection.commit()
    print(f"Додано {len(microservices_data)} записів у таблицю processed_metrics")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    load_test_data() 