import mysql.connector
import os
from dotenv import load_dotenv

# Завантаження змінних середовища з .env файлу
load_dotenv()

def clean_processed_metrics():
    """
    Очищення таблиці processed_metrics від даних RAM за певну дату
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
        # Видалення записів
        query = """
        DELETE FROM processed_metrics 
        WHERE date = '2015-10-05' AND metric_type = 'RAM'
        """
        cursor.execute(query)
        
        # Зберігаємо зміни
        connection.commit()
        print(f"Видалено {cursor.rowcount} записів з таблиці processed_metrics")
        
    except Exception as e:
        connection.rollback()
        print(f"Помилка при видаленні даних: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    clean_processed_metrics() 