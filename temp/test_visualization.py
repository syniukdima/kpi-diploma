from visualization import Visualizer
from db_input import DBInput
from group_finder import form_multiple_knapsack_groups, split_microservice_load

def test_visualization():
    """
    Тестування функцій візуалізації
    """
    # Отримання даних з бази даних
    db_input = DBInput()
    date = '2015-05-10'
    time = '19:00:00'
    metric_type = 'CPU'
    
    microservices, service_names = db_input.get_data_for_algorithm(metric_type, date, time)
    db_input.close()
    
    print(f"Отримано дані для {len(microservices)} мікросервісів")
    
    # Формування груп
    groups, group_services, slot_sums = form_multiple_knapsack_groups(microservices, max_group_size=4)
    
    # Створення візуалізатора
    visualizer = Visualizer()
    
    # Тест 1: Візуалізація часових рядів мікросервісів
    print("\nТест 1: Візуалізація часових рядів мікросервісів")
    visualizer.visualize_microservices(microservices, service_names)
    
    # Тест 2: Візуалізація загального навантаження груп
    print("\nТест 2: Візуалізація загального навантаження груп")
    visualizer.visualize_group_load(groups, group_services, service_names)
    
    # Тест 3: Візуалізація порівняння стабільності груп
    print("\nТест 3: Візуалізація порівняння стабільності груп")
    visualizer.visualize_stability_comparison(groups)
    
    # Тест 4: Візуалізація статистики по групах
    print("\nТест 4: Візуалізація статистики по групах")
    visualizer.visualize_group_statistics(groups, group_services, service_names)
    
    # Тест 5: Візуалізація базових та пікових компонентів
    print("\nТест 5: Візуалізація базових та пікових компонентів")
    
    # Знаходимо мікросервіси, які були розділені на базові та пікові компоненти
    # Аналізуємо результати групування
    split_indices = set()
    
    for group in group_services:
        for idx in group:
            if idx >= 1000 or idx < 0:  # Базовий або піковий компонент
                # Визначаємо реальний індекс
                real_idx = idx - 1000 if idx >= 1000 else -idx
                split_indices.add(real_idx)
    
    print(f"Мікросервіси, які були розділені: {[service_names[idx] for idx in split_indices]}")
    
    # Підготовка даних для візуалізації
    base_services = []
    peak_services = []
    split_names = []
    
    for idx in split_indices:
        base, peak = split_microservice_load(microservices[idx])
        base_services.append(base)
        peak_services.append(peak)
        split_names.append(service_names[idx])
    
    if base_services and peak_services:
        visualizer.visualize_base_peak_components(base_services, peak_services, split_names)
    else:
        print("Немає мікросервісів, які були розділені на базові та пікові компоненти")

if __name__ == "__main__":
    test_visualization() 