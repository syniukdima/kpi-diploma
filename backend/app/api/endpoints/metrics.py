from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
from shared.db_input import DBInput
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
    time: str = Query(..., description="Час у форматі HH:MM:SS"),
    normalization_type: Optional[str] = Query(None, description="Тип нормалізації (standard, minmax, robust, percentage)")
):
    """
    Отримання даних метрик для вибраних параметрів
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time, normalization_type
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
        
        # Запит на отримання всіх унікальних дат
        query_dates = "SELECT DISTINCT date FROM processed_metrics ORDER BY date"
        db_input.cursor.execute(query_dates)
        dates = [row["date"].strftime("%Y-%m-%d") for row in db_input.cursor.fetchall()]
        
        # Запит на отримання всіх унікальних часів для кожної дати
        times_by_date = {}
        for date in dates:
            times_by_date[date] = []
            
            # Отримуємо часи для всіх типів метрик
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