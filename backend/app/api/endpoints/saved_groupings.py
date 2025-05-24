from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import pymysql
import json
from datetime import datetime, date
import numpy as np

# Додавання шляху до кореню проекту
sys.path.append(os.path.abspath("../.."))

from shared.db_output import DBOutput

router = APIRouter()

# Ініціалізація підключення до БД
def get_db_output():
    try:
        db_output = DBOutput()
        yield db_output
    finally:
        db_output.close()

class GroupingData(BaseModel):
    date: str
    time: str
    metric_type: str
    num_groups: int

class GroupService(BaseModel):
    service_name: str
    component_type: str

@router.get("/groupings", response_model=List[GroupingData])
async def get_groupings(db_output: DBOutput = Depends(get_db_output)):
    """
    Отримує список збережених варіантів групування
    """
    try:
        # Запит до БД для отримання списку збережених варіантів групування
        query = """
        SELECT 
            date, 
            time, 
            metric_type, 
            COUNT(DISTINCT group_id) AS num_groups
        FROM grouping_results
        GROUP BY date, time, metric_type
        ORDER BY date DESC, time DESC
        """
        
        db_output.cursor.execute(query)
        results = db_output.cursor.fetchall()
        
        # Перетворення результатів у формат відповіді
        groupings = []
        for row in results:
            date_str = row["date"].strftime("%Y-%m-%d") if isinstance(row["date"], date) else str(row["date"])
            groupings.append({
                "date": date_str,
                "time": str(row["time"]),
                "metric_type": row["metric_type"],
                "num_groups": row["num_groups"]
            })
        
        return groupings
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні списку групувань: {str(e)}")

@router.get("/groups", response_model=List[int])
async def get_groups(
    date: str = Query(..., description="Дата групування у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час групування"),
    metric_type: str = Query(..., description="Тип метрики"),
    db_output: DBOutput = Depends(get_db_output)
):
    """
    Отримує список груп для вибраного варіанту групування
    """
    try:
        # Запит до БД для отримання груп
        query = """
        SELECT DISTINCT group_id
        FROM grouping_results
        WHERE date = %s AND time = %s AND metric_type = %s
        ORDER BY group_id
        """
        
        db_output.cursor.execute(query, (date, time, metric_type))
        results = db_output.cursor.fetchall()
        
        # Перетворення результатів у формат відповіді
        groups = [row["group_id"] for row in results]
        
        return groups
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні груп: {str(e)}")

@router.get("/services", response_model=List[GroupService])
async def get_services(
    date: str = Query(..., description="Дата групування у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час групування"),
    metric_type: str = Query(..., description="Тип метрики"),
    group_id: int = Query(..., description="ID групи"),
    db_output: DBOutput = Depends(get_db_output)
):
    """
    Отримує список мікросервісів для вибраної групи
    """
    try:
        # Запит до БД для отримання мікросервісів
        query = """
        SELECT service_name, component_type
        FROM grouping_results
        WHERE date = %s AND time = %s AND metric_type = %s AND group_id = %s
        ORDER BY service_name
        """
        
        db_output.cursor.execute(query, (date, time, metric_type, group_id))
        results = db_output.cursor.fetchall()
        
        # Перетворення результатів у формат відповіді
        services = []
        for row in results:
            services.append({
                "service_name": row["service_name"],
                "component_type": row["component_type"]
            })
        
        return services
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні мікросервісів: {str(e)}")

@router.get("/load", response_model=Dict[str, Any])
async def get_group_load(
    date: str = Query(..., description="Дата групування у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час групування"),
    metric_type: str = Query(..., description="Тип метрики"),
    group_id: int = Query(..., description="ID групи"),
    db_output: DBOutput = Depends(get_db_output)
):
    """
    Отримує дані навантаження для вибраної групи
    """
    try:
        # Запит до БД для отримання даних навантаження
        query = """
        SELECT service_name, component_type, load_data
        FROM grouping_results
        WHERE date = %s AND time = %s AND metric_type = %s AND group_id = %s
        ORDER BY service_name
        """
        
        db_output.cursor.execute(query, (date, time, metric_type, group_id))
        results = db_output.cursor.fetchall()
        
        services_load = {}
        for row in results:
            service_name = row["service_name"]
            component_type = row["component_type"]
            load_data = json.loads(row["load_data"]) if isinstance(row["load_data"], str) else row["load_data"]
            
            services_load[service_name] = {
                "component_type": component_type,
                "load_data": load_data
            }
        
        return {
            "group_id": group_id,
            "services": services_load
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні даних навантаження: {str(e)}")

@router.get("/statistics", response_model=Dict[str, Any])
async def get_group_statistics(
    date: str = Query(..., description="Дата групування у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час групування"),
    metric_type: str = Query(..., description="Тип метрики"),
    db_output: DBOutput = Depends(get_db_output)
):
    """
    Отримує статистику для всіх груп
    """
    try:
        # Запит до БД для отримання статистики всіх груп
        query = """
        SELECT 
            group_id,
            service_name, 
            component_type, 
            load_data,
            stability_coefficient
        FROM grouping_results
        WHERE date = %s AND time = %s AND metric_type = %s
        ORDER BY group_id, service_name
        """
        
        db_output.cursor.execute(query, (date, time, metric_type))
        results = db_output.cursor.fetchall()
        
        if not results:
            raise HTTPException(status_code=404, detail="Групи не знайдені")
        
        # Групуємо результати по group_id
        groups_data = {}
        for row in results:
            group_id = row["group_id"]
            if group_id not in groups_data:
                groups_data[group_id] = {
                    "services": [],
                    "loads": []
                }
            
            service_name = row["service_name"]
            component_type = row["component_type"]
            load_data = json.loads(row["load_data"]) if isinstance(row["load_data"], str) else row["load_data"]
            
            groups_data[group_id]["services"].append({
                "name": service_name,
                "component_type": component_type
            })
            groups_data[group_id]["loads"].append(load_data)
        
        # Формуємо статистику для кожної групи
        statistics = []
        for group_id, data in groups_data.items():
            service_loads = data["loads"]
            total_load = np.sum(service_loads, axis=0).tolist() if service_loads else []
            
            # Обчислення статистики
            if total_load:
                mean_load = np.mean(total_load)
                max_load = np.max(total_load)
                std_dev = np.std(total_load)
                cv = (std_dev / mean_load * 100) if mean_load > 0 else 0
            else:
                mean_load = 0
                max_load = 0
                cv = 0
            
            statistics.append({
                "group_id": group_id,
                "num_services": len(data["services"]),
                "services": [s["name"] for s in data["services"]],
                "mean_load": round(mean_load, 2),
                "peak_load": round(max_load, 2),
                "stability": round(cv, 2)
            })
        
        return {"statistics": statistics}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні статистики: {str(e)}") 