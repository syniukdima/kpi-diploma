from fastapi import APIRouter, Query, HTTPException, Body
from typing import List, Dict, Any, Optional
from shared.db_input import DBInput
from shared.db_output import DBOutput
from shared.group_finder import form_multiple_knapsack_groups, split_microservice_load
from pydantic import BaseModel

router = APIRouter()

# Моделі даних
class GroupingRequest(BaseModel):
    metric_type: str
    date: str
    time: str
    max_group_size: int = 4
    stability_threshold: float = 20.0
    normalization_type: Optional[str] = None

class ServiceItem(BaseModel):
    service_name: str
    values: List[float]
    component_type: str = "original"  # original, base, peak

class GroupItem(BaseModel):
    group_id: int
    services: List[ServiceItem]
    total_load: List[float]
    stability: float

class GroupingResponse(BaseModel):
    groups: List[GroupItem]
    metrics_info: Dict[str, Any]

@router.post("/run", response_model=GroupingResponse)
async def run_grouping(request: GroupingRequest):
    """
    Запуск алгоритму групування мікросервісів
    """
    try:
        db_input = DBInput()
        db_output = DBOutput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            request.metric_type, request.date, request.time, request.normalization_type
        )
        
        if not microservices:
            raise HTTPException(status_code=404, detail="Немає даних для вибраних параметрів")
        
        # Формування груп
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices, 
            max_group_size=request.max_group_size, 
            stability_threshold=request.stability_threshold
        )
        
        # Збереження результатів в базу даних
        records_count = db_output.save_grouping_results(
            groups, 
            group_services, 
            service_names, 
            request.metric_type, 
            request.date, 
            request.time
        )
        
        # Формування відповіді
        from shared.group_finder import calculate_stability
        
        result_groups = []
        for i, (group, service_indices) in enumerate(zip(groups, group_services)):
            services = []
            
            for j, (service, idx) in enumerate(zip(group, service_indices)):
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
                
                services.append(ServiceItem(
                    service_name=service_name,
                    values=service,
                    component_type=component_type
                ))
            
            # Обчислення стабільності групи
            stability = calculate_stability(group)
            
            result_groups.append(GroupItem(
                group_id=i+1,
                services=services,
                total_load=slot_sums[i],
                stability=stability
            ))
        
        # Закриття з'єднань з базою даних
        db_input.close()
        db_output.close()
        
        return GroupingResponse(
            groups=result_groups,
            metrics_info={
                "metric_type": request.metric_type,
                "date": request.date,
                "time": request.time,
                "max_group_size": request.max_group_size,
                "stability_threshold": request.stability_threshold,
                "normalization_type": request.normalization_type or "standard",
                "groups_count": len(groups),
                "services_count": len(microservices),
                "saved_records": records_count
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при групуванні мікросервісів: {str(e)}")

@router.get("/saved", response_model=List[Dict[str, Any]])
async def get_saved_groupings():
    """
    Отримання списку збережених варіантів групування
    """
    try:
        db_output = DBOutput()
        
        # Запит для отримання доступних варіантів групування
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
        
        # Форматування результатів
        groupings = []
        for row in results:
            date_str = row["date"].strftime("%Y-%m-%d")
            
            # Форматування часу
            if hasattr(row["time"], "strftime"):
                time_str = row["time"].strftime("%H:%M:%S")
            else:
                # Якщо це timedelta або інший тип
                total_seconds = int(row["time"].total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            groupings.append({
                "date": date_str,
                "time": time_str,
                "metric_type": row["metric_type"],
                "num_groups": row["num_groups"]
            })
        
        db_output.close()
        return groupings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні збережених варіантів групування: {str(e)}")

@router.get("/saved/{date}/{time}/{metric_type}", response_model=GroupingResponse)
async def get_saved_grouping(date: str, time: str, metric_type: str):
    """
    Отримання збереженого варіанту групування
    """
    try:
        db_input = DBInput()
        db_output = DBOutput()
        
        # Отримання даних мікросервісів
        microservices, service_names = db_input.get_data_for_algorithm(metric_type, date, time)
        
        # Отримання груп з бази даних
        query = """
        SELECT DISTINCT group_id
        FROM grouping_results
        WHERE date = %s AND time = %s AND metric_type = %s
        ORDER BY group_id
        """
        
        db_output.cursor.execute(query, (date, time, metric_type))
        group_ids = [row["group_id"] for row in db_output.cursor.fetchall()]
        
        result_groups = []
        for group_id in group_ids:
            # Отримання мікросервісів для поточної групи
            query = """
            SELECT service_name, component_type
            FROM grouping_results
            WHERE date = %s AND time = %s AND metric_type = %s AND group_id = %s
            """
            
            db_output.cursor.execute(query, (date, time, metric_type, group_id))
            services_in_group = db_output.cursor.fetchall()
            
            # Формування групи
            group_services = []
            group_values = []
            
            for service_row in services_in_group:
                service_name = service_row["service_name"]
                component_type = service_row["component_type"]
                
                # Знаходження індексу мікросервісу
                if service_name in service_names:
                    service_idx = service_names.index(service_name)
                    
                    # Отримання часового ряду в залежності від типу компоненту
                    if component_type == "original":
                        values = microservices[service_idx]
                    elif component_type == "base":
                        base, _ = split_microservice_load(microservices[service_idx])
                        values = base
                    elif component_type == "peak":
                        _, peak = split_microservice_load(microservices[service_idx])
                        values = peak
                    else:
                        continue
                    
                    group_services.append(ServiceItem(
                        service_name=service_name,
                        values=values,
                        component_type=component_type
                    ))
                    
                    group_values.append(values)
            
            # Обчислення загального навантаження групи
            if group_values:
                time_slots = len(group_values[0])
                total_load = [0] * time_slots
                
                for service in group_values:
                    for t in range(time_slots):
                        total_load[t] += service[t]
                
                # Обчислення стабільності групи
                from shared.group_finder import calculate_stability
                stability = calculate_stability(group_values)
                
                result_groups.append(GroupItem(
                    group_id=group_id,
                    services=group_services,
                    total_load=total_load,
                    stability=stability
                ))
        
        # Закриття з'єднань з базою даних
        db_input.close()
        db_output.close()
        
        return GroupingResponse(
            groups=result_groups,
            metrics_info={
                "metric_type": metric_type,
                "date": date,
                "time": time,
                "groups_count": len(result_groups),
                "services_count": len(microservices),
                "loaded_from_db": True
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні збереженого варіанту групування: {str(e)}") 

@router.get("/form-groups")
async def form_groups(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS"),
    max_group_size: int = Query(4, description="Максимальний розмір групи"),
    stability_threshold: float = Query(20.0, description="Поріг стабільності (%)"),
    normalization_type: Optional[str] = Query(None, description="Тип нормалізації")
):
    """
    Формування груп мікросервісів (GET версія)
    """
    try:
        db_input = DBInput()
        db_output = DBOutput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time, normalization_type
        )
        
        if not microservices:
            raise HTTPException(status_code=404, detail="Немає даних для вибраних параметрів")
        
        # Формування груп
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices, 
            max_group_size=max_group_size, 
            stability_threshold=stability_threshold
        )
        
        # Збереження результатів в базу даних
        db_output.save_grouping_results(
            groups, 
            group_services, 
            service_names, 
            metric_type, 
            date, 
            time
        )
        
        # Формування спрощеної відповіді для фронтенду
        result_groups = []
        for i, (group, service_indices) in enumerate(zip(groups, group_services)):
            group_services_list = []
            
            for idx in service_indices:
                if idx >= 1000:  # Базовий компонент
                    real_idx = idx - 1000
                    service_name = f"{service_names[real_idx]} (базовий)"
                elif idx < 0:  # Піковий компонент
                    real_idx = -idx
                    service_name = f"{service_names[real_idx]} (піковий)"
                else:  # Звичайний мікросервіс
                    service_name = service_names[idx]
                
                group_services_list.append(service_name)
            
            result_groups.append({
                "id": i+1,
                "services": group_services_list
            })
        
        # Закриття з'єднань з базою даних
        db_input.close()
        db_output.close()
        
        return {"groups": result_groups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при групуванні мікросервісів: {str(e)}")

@router.get("/find-split-services")
async def find_split_services(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS"),
    max_group_size: int = Query(4, description="Максимальний розмір групи"),
    stability_threshold: float = Query(20.0, description="Поріг стабільності (%)"),
    normalization_type: Optional[str] = Query(None, description="Тип нормалізації")
):
    """
    Знаходження мікросервісів, які були розділені на базові та пікові компоненти
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time, normalization_type
        )
        
        db_input.close()
        
        if not microservices:
            raise HTTPException(status_code=404, detail="Немає даних для вибраних параметрів")
        
        # Формування груп для знаходження розділених мікросервісів
        from shared.group_finder import form_multiple_knapsack_groups
        groups, group_services, _ = form_multiple_knapsack_groups(
            microservices, 
            max_group_size=max_group_size, 
            stability_threshold=stability_threshold
        )
        
        # Знаходження мікросервісів, які розділені на базові та пікові компоненти
        split_indices = set()
        
        for group in group_services:
            for idx in group:
                if idx >= 1000 or idx < 0:  # Базовий або піковий компонент
                    # Визначаємо реальний індекс
                    real_idx = idx - 1000 if idx >= 1000 else -idx
                    if 0 <= real_idx < len(service_names):
                        split_indices.add(real_idx)
        
        # Отримання назв розділених мікросервісів
        split_services = [service_names[idx] for idx in split_indices]
        
        return {"split_services": split_services}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при пошуку розділених мікросервісів: {str(e)}") 