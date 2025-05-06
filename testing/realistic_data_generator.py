import random
import numpy as np
import json
import os

def generate_constant_service(base_load=2, variation=0.5):
    """
    Генерує мікросервіс з майже постійним навантаженням.
    
    Args:
        base_load: Базове навантаження
        variation: Максимальне відхилення від базового навантаження
        
    Returns:
        Список з 24 значень навантаження
    """
    return [max(1, round(random.uniform(base_load - variation, base_load + variation), 1)) for _ in range(24)]

def generate_day_service(min_load=1, max_load=5):
    """
    Генерує мікросервіс з денним патерном навантаження.
    Пікові години: 9-18 (робочий день)
    
    Returns:
        Список з 24 значень навантаження
    """
    loads = []
    for hour in range(24):
        if 0 <= hour < 6:  # Нічний мінімум
            load = random.uniform(min_load, min_load + 0.5)
        elif 6 <= hour < 9:  # Ранковий підйом
            progress = (hour - 6) / 3
            load = min_load + progress * (max_load - min_load)
        elif 9 <= hour < 18:  # Денний пік
            load = random.uniform(max_load - 1, max_load)
        elif 18 <= hour < 22:  # Вечірній спад
            progress = (hour - 18) / 4
            load = max_load - progress * (max_load - min_load)
        else:  # Нічний спад
            load = random.uniform(min_load, min_load + 1)
        loads.append(max(1, round(load, 1)))
    return loads

def generate_night_service(min_load=1, max_load=5):
    """
    Генерує мікросервіс з нічним патерном навантаження.
    Пікові години: 20-4 (вечір і ніч)
    
    Returns:
        Список з 24 значень навантаження
    """
    loads = []
    for hour in range(24):
        if 0 <= hour < 4:  # Нічний пік
            load = random.uniform(max_load - 1, max_load)
        elif 4 <= hour < 8:  # Ранковий спад
            progress = (hour - 4) / 4
            load = max_load - progress * (max_load - min_load)
        elif 8 <= hour < 16:  # Денний мінімум
            load = random.uniform(min_load, min_load + 1)
        elif 16 <= hour < 20:  # Вечірній підйом
            progress = (hour - 16) / 4
            load = min_load + progress * (max_load - min_load)
        else:  # Нічний пік
            load = random.uniform(max_load - 1, max_load)
        loads.append(max(1, round(load, 1)))
    return loads

def generate_peak_service(base_load=1, peak_load=5, peak_hour=None):
    """
    Генерує мікросервіс з різким піком навантаження в певну годину.
    
    Args:
        base_load: Базове навантаження
        peak_load: Пікове навантаження
        peak_hour: Година піку (якщо None, вибирається випадково)
        
    Returns:
        Список з 24 значень навантаження
    """
    if peak_hour is None:
        peak_hour = random.randint(0, 23)
    
    loads = []
    for hour in range(24):
        if hour == peak_hour:
            load = peak_load
        elif abs(hour - peak_hour) == 1 or abs(hour - peak_hour) == 23:  # Сусідні години (з урахуванням циклічності)
            load = random.uniform(base_load + 1, peak_load - 1)
        else:
            load = random.uniform(base_load, base_load + 1)
        loads.append(max(1, round(load, 1)))
    return loads

def generate_complementary_service(service):
    """
    Генерує мікросервіс, комплементарний до заданого.
    
    Args:
        service: Список з 24 значень навантаження
        
    Returns:
        Список з 24 значень навантаження, комплементарний до вхідного
    """
    max_load = max(service)
    min_load = min(service)
    
    # Створюємо комплементарне навантаження: якщо в оригіналі високе, в результаті низьке і навпаки
    return [max(1, round(max_load + min_load - load, 1)) for load in service]

def generate_microservice_dataset(num_services, output_file=None):
    """
    Генерує набір мікросервісів з реалістичними патернами навантаження.
    
    Args:
        num_services: Кількість мікросервісів
        output_file: Файл для збереження результатів (якщо None, тільки повертає дані)
        
    Returns:
        Список списків з 24 значеннями навантаження
    """
    # Розподіл типів мікросервісів
    constant_ratio = 0.2  # 20% постійних
    day_ratio = 0.3       # 30% денних
    night_ratio = 0.2     # 20% нічних
    peak_ratio = 0.1      # 10% пікових
    complementary_ratio = 0.2  # 20% комплементарних
    
    services = []
    
    # Генеруємо постійні мікросервіси
    constant_count = int(num_services * constant_ratio)
    for _ in range(constant_count):
        base_load = random.uniform(1.5, 4)
        services.append(generate_constant_service(base_load=base_load))
    
    # Генеруємо денні мікросервіси
    day_count = int(num_services * day_ratio)
    for _ in range(day_count):
        services.append(generate_day_service())
    
    # Генеруємо нічні мікросервіси
    night_count = int(num_services * night_ratio)
    for _ in range(night_count):
        services.append(generate_night_service())
    
    # Генеруємо мікросервіси з піками
    peak_count = int(num_services * peak_ratio)
    peak_hours = random.sample(range(24), min(peak_count, 24))
    for i in range(peak_count):
        peak_hour = peak_hours[i % len(peak_hours)]
        services.append(generate_peak_service(peak_hour=peak_hour))
    
    # Генеруємо комплементарні мікросервіси
    complementary_count = int(num_services * complementary_ratio)
    source_indices = random.sample(range(len(services)), min(complementary_count, len(services)))
    for idx in source_indices:
        services.append(generate_complementary_service(services[idx]))
    
    # Додаємо випадкові мікросервіси, якщо потрібно
    while len(services) < num_services:
        service_type = random.choice(["constant", "day", "night", "peak"])
        if service_type == "constant":
            services.append(generate_constant_service())
        elif service_type == "day":
            services.append(generate_day_service())
        elif service_type == "night":
            services.append(generate_night_service())
        else:
            services.append(generate_peak_service())
    
    # Округлюємо значення до одного знаку після коми
    services = [[round(value, 1) for value in service] for service in services]
    
    # Зберігаємо в файл, якщо потрібно
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(services, f, indent=2)
        print(f"Дані збережено у файл {output_file}")
    
    return services

def plot_services(services, num_samples=5, output_file=None):
    """
    Візуалізує навантаження вибраних мікросервісів.
    
    Args:
        services: Список списків з 24 значеннями навантаження
        num_samples: Кількість мікросервісів для відображення
        output_file: Файл для збереження графіка
    """
    try:
        import matplotlib.pyplot as plt
        
        # Вибираємо випадкові мікросервіси для візуалізації
        sample_indices = random.sample(range(len(services)), min(num_samples, len(services)))
        
        plt.figure(figsize=(12, 6))
        hours = list(range(24))
        
        for idx in sample_indices:
            plt.plot(hours, services[idx], label=f"Мікросервіс {idx}")
        
        plt.xlabel("Година доби")
        plt.ylabel("Навантаження")
        plt.title("Добові патерни навантаження мікросервісів")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(range(0, 24, 2))
        plt.xlim(0, 23)
        plt.legend()
        
        if output_file:
            plt.savefig(output_file)
            print(f"Графік збережено у файл {output_file}")
        else:
            plt.show()
    
    except ImportError:
        print("Для візуалізації потрібна бібліотека matplotlib")

if __name__ == "__main__":
    # Приклад використання
    # Генеруємо 50 мікросервісів і зберігаємо у файл
    services = generate_microservice_dataset(50, "testing/microservices_data.json")
    
    # Візуалізуємо приклади мікросервісів
    try:
        plot_services(services, num_samples=8, output_file="testing/microservices_patterns.png")
    except Exception as e:
        print(f"Не вдалося створити візуалізацію: {e}")
    
    # Демонстрація різних типів
    print("\nПриклади різних типів мікросервісів:")
    print("Постійний:     ", generate_constant_service())
    print("Денний:        ", generate_day_service())
    print("Нічний:        ", generate_night_service())
    print("Піковий:       ", generate_peak_service())
    
    # Демонстрація комплементарних пар
    original = generate_day_service()
    complementary = generate_complementary_service(original)
    
    print("\nПриклад комплементарної пари:")
    print("Оригінальний:  ", original)
    print("Комплементарний:", complementary)
    print("Сума:          ", [round(a + b, 1) for a, b in zip(original, complementary)]) 