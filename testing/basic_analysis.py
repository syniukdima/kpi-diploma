import sys
import os

# Додаємо кореневу директорію проекту до шляху пошуку модулів
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import random

def generate_random_microservices(num_services, time_slots, min_load=1, max_load=5):
    """
    Генерує випадкові мікросервіси із заданими параметрами.
    """
    return [
        [random.randint(min_load, max_load) for _ in range(time_slots)]
        for _ in range(num_services)
    ]

def generate_complementary_microservices(num_services, time_slots, min_load=1, max_load=5):
    """
    Генерує мікросервіси з комплементарними патернами навантаження.
    """
    services = []
    
    # Створюємо пари мікросервісів з комплементарним навантаженням
    for i in range(num_services // 2):
        service1 = [random.randint(min_load, max_load) for _ in range(time_slots)]
        service2 = [max_load + min_load - service1[j] for j in range(time_slots)]
        services.append(service1)
        services.append(service2)
    
    # Якщо кількість мікросервісів непарна, додаємо ще один випадковий
    if num_services % 2 == 1:
        services.append([random.randint(min_load, max_load) for _ in range(time_slots)])
    
    return services

def print_test_results(test_name, microservices, groups, group_services, slot_sums):
    """
    Виводить результати тесту в форматованому вигляді.
    """
    print(f"\n{'=' * 60}")
    print(f"ТЕСТ: {test_name}")
    print(f"{'=' * 60}")
    
    print("Вхідні дані:")
    for i, service in enumerate(microservices):
        print(f"Мікросервіс {i}: {service}")
    
    print("\nРезультати розподілу груп:")
    
    group_cvs = []
    
    for i, (group, service_indices, sums) in enumerate(zip(groups, group_services, slot_sums)):
        # Обчислюємо статистики
        mean = sum(sums) / len(sums)
        variance = sum((x - mean) ** 2 for x in sums) / len(sums)
        std_dev = variance ** 0.5
        cv = (std_dev / mean) * 100 if mean > 0 else float('inf')
        group_cvs.append(cv)
        
        print(f"\nГрупа {i+1}:")
        print(f"  Мікросервіси: {service_indices}")
        print(f"  Сумарне навантаження по часових слотах: {sums}")
        print(f"  Коефіцієнт варіації: {cv:.2f}%")
    
    # Загальна статистика
    avg_cv = sum(group_cvs) / len(group_cvs) if group_cvs else 0
    
    print("\nЗагальна статистика:")
    print(f"  Кількість груп: {len(groups)}")
    print(f"  Загальна кількість мікросервісів: {sum(len(g) for g in group_services)}")
    print(f"  Середній коефіцієнт варіації: {avg_cv:.2f}%")
    print(f"  Мінімальний коефіцієнт варіації: {min(group_cvs):.2f}% (Група {group_cvs.index(min(group_cvs))+1})")
    print(f"  Максимальний коефіцієнт варіації: {max(group_cvs):.2f}% (Група {group_cvs.index(max(group_cvs))+1})")
    
    return group_cvs, avg_cv

def analyze_algorithm_performance():
    """
    Аналізує продуктивність алгоритму на різних тестових випадках.
    """
    test_results = []
    
    # Тест 1: Звичайний тест з 6 мікросервісами, 4 тайм слоти
    microservices = [
        [1, 2, 3, 4],  # Мікросервіс 0
        [4, 3, 2, 1],  # Мікросервіс 1
        [2, 2, 2, 2],  # Мікросервіс 2
        [3, 1, 4, 2],  # Мікросервіс 3
        [2, 4, 1, 3],  # Мікросервіс 4
        [3, 2, 3, 2],  # Мікросервіс 5
    ]
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Базовий тест (6 мікросервісів, 4 тайм слоти)", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Базовий тест", avg_cv))
    
    # Тест 2: Мікросервіси з ідеально комплементарними навантаженнями
    microservices = [
        [1, 5, 2, 4],  # Мікросервіс 0
        [5, 1, 4, 2],  # Мікросервіс 1 (комплементарний до 0)
        [3, 2, 5, 1],  # Мікросервіс 2
        [3, 4, 1, 5],  # Мікросервіс 3 (комплементарний до 2)
        [2, 2, 3, 4],  # Мікросервіс 4
        [4, 4, 3, 2],  # Мікросервіс 5 (комплементарний до 4)
    ]
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Комплементарні мікросервіси", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Комплементарні", avg_cv))
    
    # Тест 3: Випадкові мікросервіси
    random.seed(42)  # для відтворюваності
    microservices = generate_random_microservices(30, 6)
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Випадкові мікросервіси (30 шт, 6 тайм слотів)", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Випадкові", avg_cv))
    
    # Тест 4: Генерація комплементарних мікросервісів
    microservices = generate_complementary_microservices(8, 6)
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Згенеровані комплементарні мікросервіси (8 шт, 6 тайм слотів)", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Згенеровані комплем.", avg_cv))
    
    # Тест 5: Реалістичний сценарій з мікросервісами різних типів
    # Комбінуємо різні патерни навантаження
    microservices = []
    # Додаємо кілька зі стабільним навантаженням
    microservices.extend([[3, 3, 3, 3, 3, 3], [2, 2, 2, 2, 2, 2]])
    # Додаємо кілька з повільно змінним навантаженням
    microservices.extend([[1, 2, 2, 3, 3, 2], [3, 2, 2, 1, 1, 2]])
    # Додаємо кілька з помірними змінами
    microservices.extend([[2, 3, 4, 3, 2, 1], [1, 2, 3, 4, 3, 2]])
    # Додаємо кілька з незначними коливаннями
    microservices.extend([[2, 3, 2, 3, 2, 3], [3, 2, 3, 2, 3, 2]])
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Реалістичний сценарій з різними патернами навантаження", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Реалістичний", avg_cv))
    
    print("\nПорівняння результатів тестів:")
    for test_name, avg_cv in test_results:
        print(f"{test_name}: середній коефіцієнт варіації = {avg_cv:.2f}%")
    
    try:
        # Спроба зберегти результати у текстовий файл
        with open('testing/test_results_summary.txt', 'w', encoding='utf-8') as f:
            f.write("Порівняння результатів тестів:\n")
            for test_name, avg_cv in test_results:
                f.write(f"{test_name}: середній коефіцієнт варіації = {avg_cv:.2f}%\n")
        print("\nРезультати збережено у файл 'testing/test_results_summary.txt'")
    except Exception as e:
        print(f"\nПомилка при збереженні результатів: {e}")

if __name__ == "__main__":
    analyze_algorithm_performance() 