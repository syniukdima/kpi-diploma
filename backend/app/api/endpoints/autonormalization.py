from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import sys
import os
import json
import numpy as np

# Додавання шляху до shared модулів
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from shared.db_input import DBInput
from shared.db_output import DBOutput

router = APIRouter()

# Стандартна конфігурація сервера
STANDARD_CONFIG = {
    "CPU": {
        "value": 2.5,  # GHz
        "max_load": 100  # максимальне навантаження у відсотках
    },
    "RAM": {
        "value": 2048,  # MB (2 GB)
        "max_load": 100  # максимальне навантаження у відсотках
    },
    "CHANNEL": {
        "value": 100,  # Mbps
        "max_load": 100  # максимальне навантаження у відсотках
    }
}

class StandardServerConfig(BaseModel):
    cpu_ghz: float
    ram_gb: float
    network_mbps: float

class AnalyzeRequest(BaseModel):
    date: str
    time: str

class AutoNormalizationResult(BaseModel):
    key_resource: str
    scaling_factor: float
    message: str

@router.get("/standard-config", response_model=StandardServerConfig)
async def get_standard_config():
    """
    Отримати стандартну конфігурацію сервера
    """
    return StandardServerConfig(
        cpu_ghz=STANDARD_CONFIG["CPU"]["value"],
        ram_gb=STANDARD_CONFIG["RAM"]["value"] / 1024,  # конвертуємо MB в GB
        network_mbps=STANDARD_CONFIG["CHANNEL"]["value"]
    )

@router.post("/analyze-and-normalize", response_model=AutoNormalizationResult)
async def analyze_and_normalize(request: AnalyzeRequest):
    """
    Аналізує використання ресурсів, визначає ключовий ресурс та виконує нормалізацію
    """
    try:
        db_input = DBInput()
        db_output = DBOutput()

        # Отримуємо дані для всіх типів метрик
        metrics_data = {}
        max_percentages = {"CPU": 0, "RAM": 0, "CHANNEL": 0}
        
        for metric_type in ["CPU", "RAM", "CHANNEL"]:
            raw_data, service_names = db_input.get_raw_data_for_algorithm(
                metric_type, request.date, request.time
            )
            if not raw_data:
                continue
            
            metrics_data[metric_type] = {
                "data": raw_data,
                "services": service_names
            }
            
            # Для кожного сервісу рахуємо відсоток використання ресурсу
            for values in raw_data:
                avg_value = np.mean(values)
                if metric_type == "RAM":
                    # Для RAM конвертуємо стандартне значення в кілобайти
                    standard_value = STANDARD_CONFIG[metric_type]["value"] * 1024  # MB to KB
                else:
                    standard_value = STANDARD_CONFIG[metric_type]["value"]
                percentage = (avg_value / standard_value) * 100
                max_percentages[metric_type] = max(max_percentages[metric_type], percentage)

        if not metrics_data:
            raise HTTPException(
                status_code=404,
                detail="Немає даних для вибраних параметрів"
            )

        # Визначаємо ключовий ресурс (з найбільшим відсотком використання)
        key_resource = max(max_percentages.items(), key=lambda x: x[1])[0]
        max_percentage = max_percentages[key_resource]
        scaling_factor = max_percentage / 100 if max_percentage > 100 else 1.0

        # Нормалізуємо дані тільки для ключового ресурсу
        if scaling_factor > 1.0:
            raw_data = metrics_data[key_resource]["data"]
            service_names = metrics_data[key_resource]["services"]
            
            # Нормалізуємо значення для кожного сервісу
            for i, values in enumerate(raw_data):
                normalized_values = [v / scaling_factor for v in values]
                # Зберігаємо нормалізовані значення
                db_output.save_processed_data(
                    service_names[i],
                    key_resource,
                    request.date,
                    request.time,
                    normalized_values
                )

        # Закриваємо з'єднання
        db_input.close()
        db_output.close()

        # Формуємо повідомлення
        resource_names = {
            "CPU": "процесор",
            "RAM": "пам'ять",
            "CHANNEL": "мережа"
        }
        
        # Формуємо рядки з відсотками відхилення для кожного ресурсу
        excesses = []
        for metric_type in ["CPU", "RAM", "CHANNEL"]:  # фіксований порядок
            percentage = max_percentages[metric_type]
            # Відхилення = на скільки відсотків більше/менше від стандартного
            deviation = percentage - 100
            sign = "+" if deviation > 0 else ""  # додаємо + для позитивних чисел
            excesses.append(f"{resource_names[metric_type]}: {sign}{deviation:.1f}%")
        
        # Формуємо інформацію про стандартний сервер
        server_info = (
            f"Стандартний сервер: процесор {STANDARD_CONFIG['CPU']['value']} GHz, "
            f"пам'ять {int(STANDARD_CONFIG['RAM']['value']/1024)} GB, "
            f"мережа {STANDARD_CONFIG['CHANNEL']['value']} Mbps"
        )
        
        message = server_info + "\n\n"
        message += "Відсоток відхилення від стандартного показника: " + "; ".join(excesses)
        message += ". Нормалізацію проведено за показником: " + resource_names[key_resource]

        return AutoNormalizationResult(
            key_resource=key_resource,
            scaling_factor=scaling_factor,
            message=message
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in analyze_and_normalize: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Помилка при аналізі та нормалізації: {str(e)}"
        ) 