from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
import sys
import os

# Додавання шляху до shared модулів
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from shared.db_input import DBInput
from shared.db_output import DBOutput
from pydantic import BaseModel

router = APIRouter()

# Моделі даних
class DateItem(BaseModel):
    date: str

class TimeItem(BaseModel):
    time: str

class MetricValue(BaseModel):
    service_name: str
    values: List[float]

class MetricsResponse(BaseModel):
    microservices: List[MetricValue]

class AvailableOptions(BaseModel):
    dates: List[str]
    times: Dict[str, List[str]]
    metric_types: List[str] = ["CPU", "RAM", "CHANNEL"]

@router.get("/types", response_model=List[str])
async def get_metric_types():
    """
    Отримання доступних типів метрик
    """
    return ["CPU", "RAM", "CHANNEL"]

@router.get("/dates", response_model=List[DateItem])
async def get_available_dates(metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)")):
    """
    Отримання доступних дат для вибраного типу метрики
    """
    try:
        db_input = DBInput()
        
        # Отримання списку доступних дат
        query = "SELECT DISTINCT date FROM processed_metrics WHERE metric_type = %s ORDER BY date"
        db_input.cursor.execute(query, (metric_type,))
        results = db_input.cursor.fetchall()
        
        dates = [DateItem(date=row["date"].strftime("%Y-%m-%d")) for row in results]
        
        db_input.close()
        return dates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні дат: {str(e)}")

@router.get("/times", response_model=List[TimeItem])
async def get_available_times(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD")
):
    """
    Отримання доступних часів для вибраної дати та типу метрики
    """
    try:
        db_input = DBInput()
        
        # Отримання списку доступних часів
        query = "SELECT DISTINCT time FROM processed_metrics WHERE metric_type = %s AND date = %s ORDER BY time"
        db_input.cursor.execute(query, (metric_type, date))
        results = db_input.cursor.fetchall()
        
        times = []
        for row in results:
            # Конвертація time в рядок
            if hasattr(row["time"], "strftime"):
                time_str = row["time"].strftime("%H:%M:%S")
            else:
                # Якщо це timedelta або інший тип
                total_seconds = int(row["time"].total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            times.append(TimeItem(time=time_str))
        
        db_input.close()
        return times
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні часів: {str(e)}")

@router.get("/data", response_model=MetricsResponse)
async def get_metrics_data(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS")
):
    """
    Отримання даних метрик для вибраних параметрів
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time
        )
        
        # Формування відповіді
        result = []
        for i, (service, name) in enumerate(zip(microservices, service_names)):
            result.append(MetricValue(service_name=name, values=service))
        
        db_input.close()
        return MetricsResponse(microservices=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні даних метрик: {str(e)}") 

@router.get("/available-options", response_model=AvailableOptions)
async def get_available_options():
    """
    Отримати доступні дати, часи та типи метрик для вибору
    """
    try:
        db_input = DBInput()
        metric_types = ["CPU", "RAM", "CHANNEL"]
        
        # Запит на отримання всіх унікальних дат з raw_metrics
        query_dates = "SELECT DISTINCT date FROM raw_metrics ORDER BY date"
        db_input.cursor.execute(query_dates)
        raw_dates = [row["date"].strftime("%Y-%m-%d") for row in db_input.cursor.fetchall()]
        
        # Також отримуємо дати з processed_metrics для повного списку
        query_dates = "SELECT DISTINCT date FROM processed_metrics ORDER BY date"
        db_input.cursor.execute(query_dates)
        processed_dates = [row["date"].strftime("%Y-%m-%d") for row in db_input.cursor.fetchall()]
        
        # Об'єднуємо дати з обох таблиць без дублікатів
        dates = list(set(raw_dates + processed_dates))
        dates.sort()
        
        # Запит на отримання всіх унікальних часів для кожної дати
        times_by_date = {}
        for date in dates:
            times_by_date[date] = []
            
            # Отримуємо часи з raw_metrics для всіх типів метрик
            for metric_type in metric_types:
                query_times = "SELECT DISTINCT time FROM raw_metrics WHERE date = %s AND metric_type = %s ORDER BY time"
                db_input.cursor.execute(query_times, (date, metric_type))
                
                # Додаємо унікальні часи у список
                for row in db_input.cursor.fetchall():
                    # Конвертація time в рядок
                    if hasattr(row["time"], "strftime"):
                        time_str = row["time"].strftime("%H:%M:%S")
                    else:
                        # Якщо це timedelta або інший тип
                        total_seconds = int(row["time"].total_seconds())
                        hours, remainder = divmod(total_seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    if time_str not in times_by_date[date]:
                        times_by_date[date].append(time_str)
            
            # Отримуємо часи з processed_metrics для всіх типів метрик, якщо немає даних з raw_metrics
            if not times_by_date[date]:
                for metric_type in metric_types:
                    query_times = "SELECT DISTINCT time FROM processed_metrics WHERE date = %s AND metric_type = %s ORDER BY time"
                    db_input.cursor.execute(query_times, (date, metric_type))
                    
                    # Додаємо унікальні часи у список
                    for row in db_input.cursor.fetchall():
                        # Конвертація time в рядок
                        if hasattr(row["time"], "strftime"):
                            time_str = row["time"].strftime("%H:%M:%S")
                        else:
                            # Якщо це timedelta або інший тип
                            total_seconds = int(row["time"].total_seconds())
                            hours, remainder = divmod(total_seconds, 3600)
                            minutes, seconds = divmod(remainder, 60)
                            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        
                        if time_str not in times_by_date[date]:
                            times_by_date[date].append(time_str)
            
            # Сортуємо часи
            times_by_date[date].sort()
        
        db_input.close()
        
        return AvailableOptions(
            dates=dates,
            times=times_by_date,
            metric_types=metric_types
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні доступних опцій: {str(e)}") 

@router.post("/normalize-percentage")
async def normalize_data_to_percentage(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS")
):
    """
    Нормалізує сирі дані мікросервісів до відсотків (0-100) і зберігає їх у таблицю processed_metrics.
    """
    try:
        # Ініціалізація з'єднань з БД
        db_input = DBInput()
        db_output = DBOutput()
        
        # Отримання даних для алгоритму
        raw_data, service_names = db_input.get_raw_data_for_algorithm(
            metric_type, date, time
        )
        
        if not raw_data:
            # Перевіряємо, які дані є в таблиці raw_metrics
            query = "SELECT DISTINCT date, time FROM raw_metrics WHERE metric_type = %s ORDER BY date, time LIMIT 5"
            db_input.cursor.execute(query, (metric_type,))
            available_options = db_input.cursor.fetchall()
            
            available_options_str = ""
            if available_options:
                available_options_str = "\nДоступні опції для типу метрики " + metric_type + ":\n"
                for option in available_options:
                    date_str = option["date"].strftime("%Y-%m-%d") if hasattr(option["date"], "strftime") else str(option["date"])
                    time_str = option["time"].strftime("%H:%M:%S") if hasattr(option["time"], "strftime") else str(option["time"])
                    available_options_str += f"- Дата: {date_str}, Час: {time_str}\n"
            
            db_input.close()
            db_output.close()
            raise HTTPException(
                status_code=404, 
                detail=f"Немає даних для вибраних параметрів: Тип: {metric_type}, Дата: {date}, Час: {time}. {available_options_str}"
            )
        
        # Нормалізація та збереження кожного мікросервісу
        processed_count = 0
        for i, service_name in enumerate(service_names):
            raw_values = raw_data[i]
            if db_output.process_and_save_percentage_data(
                service_name, metric_type, date, time, raw_values
            ):
                processed_count += 1
        
        # Закриття з'єднань
        db_input.close()
        db_output.close()
        
        return {
            "status": "success",
            "message": f"Дані успішно нормалізовані та збережені для {processed_count} мікросервісів",
            "processed_count": processed_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при нормалізації даних: {str(e)}") 

@router.get("/raw-data-options", response_model=AvailableOptions)
async def get_raw_data_options():
    """
    Отримати доступні дати, часи та типи метрик з таблиці raw_metrics для нормалізації
    """
    try:
        db_input = DBInput()
        metric_types = ["CPU", "RAM", "CHANNEL"]
        
        # Запит на отримання всіх унікальних дат з raw_metrics
        query_dates = "SELECT DISTINCT date FROM raw_metrics ORDER BY date"
        db_input.cursor.execute(query_dates)
        dates = [row["date"].strftime("%Y-%m-%d") for row in db_input.cursor.fetchall()]
        
        # Запит на отримання всіх унікальних часів для кожної дати
        times_by_date = {}
        for date in dates:
            times_by_date[date] = []
            
            # Отримуємо часи з raw_metrics для всіх типів метрик
            for metric_type in metric_types:
                query_times = "SELECT DISTINCT time FROM raw_metrics WHERE date = %s AND metric_type = %s ORDER BY time"
                db_input.cursor.execute(query_times, (date, metric_type))
                
                # Додаємо унікальні часи у список
                for row in db_input.cursor.fetchall():
                    # Конвертація time в рядок
                    if hasattr(row["time"], "strftime"):
                        time_str = row["time"].strftime("%H:%M:%S")
                    else:
                        # Якщо це timedelta або інший тип
                        total_seconds = int(row["time"].total_seconds())
                        hours, remainder = divmod(total_seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    if time_str not in times_by_date[date]:
                        times_by_date[date].append(time_str)
            
            # Сортуємо часи
            times_by_date[date].sort()
        
        db_input.close()
        
        return AvailableOptions(
            dates=dates,
            times=times_by_date,
            metric_types=metric_types
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні доступних опцій: {str(e)}") 