from fastapi import APIRouter, Query, HTTPException, Response, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from shared.db_input import DBInput
import io
import matplotlib.pyplot as plt
import numpy as np

router = APIRouter()

# Моделі даних
class TimeSeriesPoint(BaseModel):
    x: int  # Індекс точки (часовий слот)
    y: float  # Значення

class TimeSeriesData(BaseModel):
    name: str  # Назва серії
    data: List[TimeSeriesPoint]

class ChartData(BaseModel):
    series: List[TimeSeriesData]
    title: str
    xlabel: str = "Часовий слот"
    ylabel: str = "Навантаження"

class StabilityRequest(BaseModel):
    groups: List[List[List[float]]]
    group_ids: Optional[List[int]] = None

class StabilityChartData(BaseModel):
    labels: List[str]
    data: List[float]
    title: str
    xlabel: str
    ylabel: str

class GroupStatistics(BaseModel):
    group_id: int
    num_services: int
    mean_load: float
    peak_load: float
    stability: float
    services: List[str]

class GroupStatisticsResponse(BaseModel):
    statistics: List[GroupStatistics]

@router.get("/microservices", response_model=ChartData)
async def get_microservices_chart(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS")
):
    """
    Отримання даних для графіку часових рядів мікросервісів
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time
        )
        
        db_input.close()
        
        if not microservices:
            raise HTTPException(status_code=404, detail="Немає даних для вибраних параметрів")
        
        # Формування даних для графіку
        series = []
        for i, (service, name) in enumerate(zip(microservices, service_names)):
            data = [TimeSeriesPoint(x=j, y=val) for j, val in enumerate(service)]
            series.append(TimeSeriesData(name=name, data=data))
        
        return ChartData(
            series=series,
            title=f"Часові ряди мікросервісів ({metric_type}, {date}, {time})"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні даних для графіку: {str(e)}")

@router.get("/split/{service_name}", response_model=ChartData)
async def get_split_chart(
    service_name: str,
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS")
):
    """
    Отримання даних для графіку розділення мікросервісу на базовий та піковий компоненти
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time
        )
        
        db_input.close()
        
        if not microservices or service_name not in service_names:
            raise HTTPException(status_code=404, detail="Мікросервіс не знайдено")
        
        # Знаходження індексу мікросервісу
        service_idx = service_names.index(service_name)
        service_data = microservices[service_idx]
        
        # Розділення на базовий та піковий компоненти
        from shared.group_finder import split_microservice_load
        base, peak = split_microservice_load(service_data)
        
        # Формування даних для графіку
        series = []
        
        # Базовий компонент
        base_data = [TimeSeriesPoint(x=i, y=val) for i, val in enumerate(base)]
        series.append(TimeSeriesData(name="Базовий компонент", data=base_data))
        
        # Піковий компонент
        peak_data = [TimeSeriesPoint(x=i, y=val) for i, val in enumerate(peak)]
        series.append(TimeSeriesData(name="Піковий компонент", data=peak_data))
        
        return ChartData(
            series=series,
            title=f"Розділення навантаження {service_name} ({metric_type}, {date}, {time})"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні даних для графіку: {str(e)}")

@router.post("/stability")
async def get_stability_chart(request: StabilityRequest):
    """
    Отримання зображення графіку стабільності груп
    """
    try:
        from shared.visualization import Visualizer
        from shared.group_finder import calculate_stability
        
        # Створення об'єкта візуалізатора
        visualizer = Visualizer()
        
        # Перехоплення виводу matplotlib
        buf = io.BytesIO()
        
        # Ручне створення рисунка замість виклику методу visualizer
        # Це дозволяє нам перехопити графік, не показуючи його
        plt.figure(figsize=visualizer.figsize)
        
        cv_values = []
        group_labels = []
        
        for i, group in enumerate(request.groups):
            # Обчислення коефіцієнта варіації
            time_slots = len(group[0]) if group else 0
            total_load = [0] * time_slots
            
            for service in group:
                for t in range(time_slots):
                    total_load[t] += service[t]
            
            # Обчислення коефіцієнта варіації
            mean = np.mean(total_load)
            std_dev = np.std(total_load)
            cv = (std_dev / mean) * 100 if mean > 0 else float('inf')
            
            cv_values.append(cv if cv != float('inf') else 100)  # Обмеження для візуалізації
            group_labels.append(f"Група {i+1}")
        
        # Побудова графіка
        plt.bar(group_labels, cv_values)
        plt.title("Порівняння стабільності груп за коефіцієнтом варіації")
        plt.xlabel("Група")
        plt.ylabel("Коефіцієнт варіації (%)")
        plt.grid(True, axis='y')
        plt.tight_layout()
        
        # Збереження в байтовий буфер замість відображення
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Закриття фігури щоб уникнути витоку пам'яті
        plt.close()
        
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при обчисленні стабільності груп: {str(e)}")

@router.get("/group-load")
async def get_group_load_chart(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS"),
    max_group_size: int = Query(4, description="Максимальний розмір групи"),
    stability_threshold: float = Query(20.0, description="Поріг стабільності (%)")
):
    """
    Отримання графіку загального навантаження груп у форматі PNG
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time
        )
        
        db_input.close()
        
        if not microservices:
            raise HTTPException(status_code=404, detail="Немає даних для вибраних параметрів")
        
        # Формування груп
        from shared.group_finder import form_multiple_knapsack_groups
        from shared.visualization import Visualizer
        
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices, 
            max_group_size=max_group_size, 
            stability_threshold=stability_threshold
        )
        
        # Створення візуалізатора
        visualizer = Visualizer()
        
        # Перехоплення виводу matplotlib
        buf = io.BytesIO()
        
        # Ручне створення рисунка аналогічно методу visualize_group_load
        plt.figure(figsize=visualizer.figsize)
        
        for i, (group, total_load) in enumerate(zip(groups, slot_sums)):
            # Побудова графіка для групи
            plt.plot(total_load, label=f"Група {i+1}", marker='o', linestyle='-', markersize=4)
        
        plt.title(f"Загальне навантаження груп ({metric_type}, {date}, {time})")
        plt.xlabel("Часовий слот")
        plt.ylabel("Загальне навантаження")
        plt.legend(loc='best')
        plt.grid(True)
        plt.tight_layout()
        
        # Збереження в байтовий буфер замість відображення
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        
        # Закриття фігури щоб уникнути витоку пам'яті
        plt.close()
        
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні графіку: {str(e)}")

@router.get("/group-statistics", response_model=GroupStatisticsResponse)
async def get_group_statistics(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS"),
    max_group_size: int = Query(4, description="Максимальний розмір групи"),
    stability_threshold: float = Query(20.0, description="Поріг стабільності (%)")
):
    """
    Отримання статистики по групах
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time
        )
        
        db_input.close()
        
        if not microservices:
            raise HTTPException(status_code=404, detail="Немає даних для вибраних параметрів")
        
        # Формування груп
        from shared.group_finder import form_multiple_knapsack_groups, calculate_stability
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices, 
            max_group_size=max_group_size, 
            stability_threshold=stability_threshold
        )
        
        # Обчислення статистики для кожної групи
        group_stats = []
        for i, (group, service_indices, total_load) in enumerate(zip(groups, group_services, slot_sums)):
            # Сервіси у групі
            services = []
            for idx in service_indices:
                if idx >= 1000:  # Базовий компонент
                    real_idx = idx - 1000
                    services.append(f"{service_names[real_idx]} (базовий)")
                elif idx < 0:  # Піковий компонент
                    real_idx = -idx
                    services.append(f"{service_names[real_idx]} (піковий)")
                else:  # Звичайний мікросервіс
                    services.append(service_names[idx])
            
            # Обчислення статистики
            mean_load = np.mean(total_load) if total_load else 0
            peak_load = max(total_load) if total_load else 0
            stability = calculate_stability(group)
            
            group_stats.append(GroupStatistics(
                group_id=i+1,
                num_services=len(service_indices),
                mean_load=float(mean_load),  # Конвертація в float для уникнення проблем з серіалізацією numpy float
                peak_load=float(peak_load),
                stability=float(stability),
                services=services
            ))
        
        return GroupStatisticsResponse(statistics=group_stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при отриманні статистики груп: {str(e)}")

@router.get("/group-load-distribution")
async def get_load_distribution_chart(
    group_id: int = Query(..., description="ID групи"),
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS"),
    max_group_size: int = Query(4, description="Максимальний розмір групи"),
    stability_threshold: float = Query(20.0, description="Поріг стабільності (%)")
):
    """
    Отримання зображення графіку розподілу навантаження в групі за часовими слотами
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time
        )
        
        db_input.close()
        
        if not microservices:
            raise HTTPException(status_code=404, detail="Немає даних для вибраних параметрів")
        
        # Формування груп
        from shared.group_finder import form_multiple_knapsack_groups, calculate_stability
        groups, group_services, _ = form_multiple_knapsack_groups(
            microservices, 
            max_group_size=max_group_size, 
            stability_threshold=stability_threshold
        )
        
        if group_id <= 0 or group_id > len(groups):
            raise HTTPException(status_code=404, detail=f"Група {group_id} не знайдена")
        
        # Візуалізація розподілу навантаження
        buf = io.BytesIO()
        
        # Отримання даних для вибраної групи
        group_idx = group_id - 1
        group = groups[group_idx]
        service_indices = group_services[group_idx]
        
        # Визначення кількості часових слотів
        time_slots = len(group[0]) if group else 0
        
        # Створення стовпчикової діаграми для кожного часового слоту
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Знаходження максимального навантаження для групи
        max_load = 0
        for t in range(time_slots):
            slot_load = sum(service[t] for service in group)
            max_load = max(max_load, slot_load)
        
        # Кольори для кожного сервісу
        colors = plt.cm.tab20(range(len(group)))
        
        # Підготовка даних для легенди
        legend_patches = []
        
        # Формування даних для стовпчикової діаграми
        bottoms = [0] * time_slots
        for i, (service, idx) in enumerate(zip(group, service_indices)):
            # Визначення назви сервісу
            if idx >= 1000:  # Базовий компонент
                real_idx = idx - 1000
                service_name = f"{service_names[real_idx]} (базовий)"
            elif idx < 0:  # Піковий компонент
                real_idx = -idx
                service_name = f"{service_names[real_idx]} (піковий)"
            else:  # Звичайний мікросервіс
                service_name = service_names[idx]
            
            # Додавання стовпчиків для поточного сервісу
            bars = ax.bar(range(time_slots), service, bottom=bottoms, 
                         color=colors[i % len(colors)], edgecolor='black', linewidth=0.5)
            
            # Додавання патчу для легенди
            legend_patches.append(plt.Rectangle((0, 0), 1, 1, color=colors[i % len(colors)], label=service_name))
            
            # Оновлення нижньої межі для наступного сервісу
            for t in range(time_slots):
                bottoms[t] += service[t]
        
        # Додаємо "вільне місце" як прозору частину стовпчиків
        free_space = [max_load - b for b in bottoms]
        ax.bar(range(time_slots), free_space, bottom=bottoms, alpha=0.2, hatch='///', 
              edgecolor='gray', linewidth=0.5)
        legend_patches.append(plt.Rectangle((0, 0), 1, 1, alpha=0.2, hatch='///', label="Вільне місце"))
        
        # Налаштування графіка
        ax.set_title(f"Розподіл навантаження для Групи {group_id}")
        ax.set_xlabel("Часовий слот")
        ax.set_ylabel("Навантаження")
        ax.set_xticks(range(time_slots))
        ax.set_xticklabels([f"{t+1}" for t in range(time_slots)])
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Встановлюємо межі осі Y
        ax.set_ylim(0, max_load)
        
        # Додаємо легенду
        ax.legend(handles=legend_patches, loc='upper right', title="Мікросервіси")
        
        # Обчислення стабільності групи
        stability = calculate_stability(group)
        
        # Додаємо інформацію про стабільність групи як текст під графіком
        plt.figtext(0.5, 0.01, f"Коефіцієнт стабільності групи: {stability:.2f}%", 
                   ha='center', fontsize=10, fontweight='bold')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.98])  # Залишаємо місце для тексту
        
        # Збереження в байтовий буфер
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        
        # Закриття фігури
        plt.close()
        
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при створенні графіку: {str(e)}")

@router.get("/stability-direct")
async def get_stability_direct_chart(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS"),
    max_group_size: int = Query(4, description="Максимальний розмір групи"),
    stability_threshold: float = Query(20.0, description="Поріг стабільності (%)")
):
    """
    Отримання зображення графіку стабільності груп на основі даних з сервера
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time
        )
        
        db_input.close()
        
        if not microservices:
            raise HTTPException(status_code=404, detail="Немає даних для вибраних параметрів")
        
        # Формування груп
        from shared.group_finder import form_multiple_knapsack_groups, calculate_stability
        from shared.visualization import Visualizer
        
        groups, group_services, _ = form_multiple_knapsack_groups(
            microservices, 
            max_group_size=max_group_size, 
            stability_threshold=stability_threshold
        )
        
        # Фільтруємо групи з більш ніж 1 елементом для графіка стабільності
        filtered_groups = []
        filtered_group_services = []
        for i, (group, services) in enumerate(zip(groups, group_services)):
            if len(services) > 1:  # Показуємо тільки групи з більш ніж 1 елементом
                filtered_groups.append(group)
                filtered_group_services.append(services)
        
        # Якщо немає груп з більш ніж 1 елементом
        if not filtered_groups:
            raise HTTPException(status_code=404, detail="Немає груп з більш ніж одним елементом для відображення стабільності")
        
        # Створення візуалізатора
        visualizer = Visualizer()
        
        # Перехоплення виводу matplotlib
        buf = io.BytesIO()
        
        # Створення рисунка
        plt.figure(figsize=visualizer.figsize)
        
        cv_values = []
        group_labels = []
        
        for i, group in enumerate(filtered_groups):
            # Обчислення коефіцієнта варіації
            stability = calculate_stability(group)
            cv_values.append(stability if stability != float('inf') else 100)
            group_labels.append(f"Група {i+1}")
        
        # Побудова графіка
        plt.bar(group_labels, cv_values)
        plt.title("Порівняння стабільності груп за коефіцієнтом варіації")
        plt.xlabel("Група")
        plt.ylabel("Коефіцієнт варіації (%)")
        plt.grid(True, axis='y')
        plt.tight_layout()
        
        # Збереження в байтовий буфер
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        
        # Закриття фігури
        plt.close()
        
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при створенні графіку стабільності: {str(e)}")

@router.get("/microservices-chart")
async def get_microservices_chart(
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS")
):
    """
    Отримання графіку часових рядів мікросервісів у форматі PNG
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time
        )
        
        db_input.close()
        
        if not microservices:
            raise HTTPException(status_code=404, detail="Немає даних для вибраних параметрів")
        
        # Створення графіка як у десктопній версії
        from shared.visualization import Visualizer
        
        # Створення візуалізатора
        visualizer = Visualizer()
        
        # Перехоплення виводу matplotlib
        buf = io.BytesIO()
        
        # Створення рисунка
        plt.figure(figsize=visualizer.figsize)
        
        for i, (service, name) in enumerate(zip(microservices, service_names)):
            plt.plot(service, label=name, marker='o', linestyle='-', markersize=4)
        
        plt.title(f"Часові ряди мікросервісів ({metric_type}, {date}, {time})")
        plt.xlabel("Часовий слот")
        plt.ylabel("Навантаження")
        
        # Розміщення легенди збоку від графіка
        plt.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=9)
        
        plt.grid(True)
        plt.tight_layout(rect=[0, 0, 0.85, 1])  # Залишаємо простір для легенди
        
        # Збереження в буфер
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()
        
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при побудові графіку мікросервісів: {str(e)}")

@router.get("/base-peak-component")
async def get_base_peak_component_chart(
    service_name: str = Query(..., description="Назва мікросервісу"),
    metric_type: str = Query(..., description="Тип метрики (CPU, RAM, CHANNEL)"),
    date: str = Query(..., description="Дата у форматі YYYY-MM-DD"),
    time: str = Query(..., description="Час у форматі HH:MM:SS")
):
    """
    Отримання графіку розділення мікросервісу на базовий та піковий компоненти у форматі PNG
    """
    try:
        db_input = DBInput()
        
        # Отримання даних для алгоритму
        microservices, service_names = db_input.get_data_for_algorithm(
            metric_type, date, time
        )
        
        db_input.close()
        
        if not microservices or service_name not in service_names:
            raise HTTPException(status_code=404, detail="Мікросервіс не знайдено")
        
        # Знаходження індексу мікросервісу
        service_idx = service_names.index(service_name)
        service_data = microservices[service_idx]
        
        # Розділення на базовий та піковий компоненти
        from shared.group_finder import split_microservice_load
        base, peak = split_microservice_load(service_data)
        
        # Створення графіка як у десктопній версії
        from shared.visualization import Visualizer
        
        # Створення візуалізатора
        visualizer = Visualizer()
        
        # Перехоплення виводу matplotlib
        buf = io.BytesIO()
        
        # Створення рисунка
        plt.figure(figsize=visualizer.figsize)
        
        # Побудова графіків
        plt.plot(base, label="Базовий компонент", marker='o', linestyle='-', color='blue', markersize=4)
        plt.plot(peak, label="Піковий компонент", marker='x', linestyle='--', color='red', markersize=4)
        plt.plot([b + p for b, p in zip(base, peak)], label="Загальне навантаження", 
                marker='s', linestyle='-.', color='green', markersize=4)
        
        plt.title(f"Розділення навантаження для мікросервісу: {service_name}")
        plt.xlabel("Часовий слот")
        plt.ylabel("Навантаження")
        
        # Розміщення легенди збоку від графіка
        plt.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=9)
        
        plt.grid(True)
        plt.tight_layout(rect=[0, 0, 0.85, 1])  # Залишаємо простір для легенди
        
        # Збереження в буфер
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()
        
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при побудові графіку: {str(e)}") 