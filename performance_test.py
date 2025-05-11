import time
import random
import numpy as np
import matplotlib.pyplot as plt
from group_finder import form_multiple_knapsack_groups, calculate_stability

def generate_random_microservice(time_slots, pattern_type=None):
    """
    Генерує випадковий мікросервіс з заданою кількістю таймслотів та типом патерну.
    
    Args:
        time_slots: Кількість таймслотів
        pattern_type: Тип патерну ('stable', 'peak', 'complementary', 'random')
        
    Returns:
        Список навантажень мікросервісу за таймслотами
    """
    if pattern_type is None:
        pattern_type = random.choice(['stable', 'peak', 'complementary', 'random'])
    
    if pattern_type == 'stable':
        # Стабільне навантаження з невеликими коливаннями
        base_load = random.randint(1, 5)
        service = [base_load + random.randint(0, 2) for _ in range(time_slots)]
    elif pattern_type == 'peak':
        # Навантаження з піками
        base_load = random.randint(1, 3)
        service = [base_load for _ in range(time_slots)]
        # Додаємо 1-3 піки
        num_peaks = random.randint(1, 3)
        for _ in range(num_peaks):
            peak_pos = random.randint(0, time_slots - 1)
            service[peak_pos] = base_load * random.randint(5, 10)
    elif pattern_type == 'complementary':
        # Комплементарне навантаження (високе-низьке-високе)
        base_load = random.randint(1, 3)
        high_load = base_load * random.randint(5, 10)
        service = []
        for i in range(time_slots):
            if i % 2 == 0:
                service.append(high_load)
            else:
                service.append(base_load)
    else:  # random
        # Повністю випадкове навантаження
        service = [random.randint(1, 10) for _ in range(time_slots)]
    
    return service

def generate_microservices(num_services, time_slots, pattern_distribution=None):
    """
    Генерує набір мікросервісів із заданим розподілом типів патернів.
    
    Args:
        num_services: Кількість мікросервісів
        time_slots: Кількість таймслотів
        pattern_distribution: Словник з розподілом типів патернів
            Наприклад: {'stable': 0.3, 'peak': 0.4, 'complementary': 0.2, 'random': 0.1}
            
    Returns:
        Список мікросервісів
    """
    if pattern_distribution is None:
        pattern_distribution = {'stable': 0.25, 'peak': 0.25, 'complementary': 0.25, 'random': 0.25}
    
    microservices = []
    patterns = list(pattern_distribution.keys())
    weights = list(pattern_distribution.values())
    
    for _ in range(num_services):
        pattern_type = random.choices(patterns, weights=weights)[0]
        service = generate_random_microservice(time_slots, pattern_type)
        microservices.append(service)
    
    return microservices

def run_performance_test(num_services_list, time_slots, max_group_size=4, stability_threshold=20.0, 
                        pattern_distribution=None, num_runs=3):
    """
    Запускає тест продуктивності для різної кількості мікросервісів.
    
    Args:
        num_services_list: Список кількостей мікросервісів для тестування
        time_slots: Кількість таймслотів
        max_group_size: Максимальний розмір групи
        stability_threshold: Поріг стабільності
        pattern_distribution: Розподіл типів патернів
        num_runs: Кількість запусків для кожної конфігурації
        
    Returns:
        Словник з результатами тестів
    """
    results = {
        'num_services': [],
        'execution_time': [],
        'num_groups': [],
        'groups_per_second': [],
        'avg_group_size': [],
        'avg_stability': []
    }
    
    print(f"\n=== ТЕСТ ПРОДУКТИВНОСТІ ===")
    print(f"Кількість таймслотів: {time_slots}")
    print(f"Максимальний розмір групи: {max_group_size}")
    print(f"Поріг стабільності: {stability_threshold}%")
    print(f"Розподіл патернів: {pattern_distribution}")
    print(f"Кількість запусків для кожної конфігурації: {num_runs}")
    
    for num_services in num_services_list:
        print(f"\nТестування для {num_services} мікросервісів...")
        
        # Запускаємо алгоритм кілька разів і обчислюємо середні значення
        run_times = []
        run_num_groups = []
        run_groups_per_second = []
        run_avg_group_size = []
        run_avg_stability = []
        
        for run in range(num_runs):
            print(f"  Запуск {run + 1}/{num_runs}...")
            
            # Генеруємо мікросервіси
            microservices = generate_microservices(num_services, time_slots, pattern_distribution)
            
            # Вимірюємо час виконання
            start_time = time.time()
            groups, group_services, slot_sums = form_multiple_knapsack_groups(
                microservices,
                max_group_size=max_group_size,
                stability_threshold=stability_threshold
            )
            end_time = time.time()
            
            # Обчислюємо метрики
            execution_time = end_time - start_time
            num_groups = len(groups)
            groups_per_second = num_groups / execution_time if execution_time > 0 else 0
            
            # Обчислюємо середній розмір групи
            group_sizes = [len(group) for group in group_services]
            avg_group_size = sum(group_sizes) / len(group_sizes) if group_sizes else 0
            
            # Обчислюємо середню стабільність груп
            stabilities = []
            for group in groups:
                if len(group) > 1:
                    cv = calculate_stability(group)
                    if cv != float('inf'):
                        stabilities.append(cv)
            avg_stability = sum(stabilities) / len(stabilities) if stabilities else 0
            
            # Зберігаємо результати запуску
            run_times.append(execution_time)
            run_num_groups.append(num_groups)
            run_groups_per_second.append(groups_per_second)
            run_avg_group_size.append(avg_group_size)
            run_avg_stability.append(avg_stability)
        
        # Обчислюємо середні значення по всіх запусках
        avg_execution_time = sum(run_times) / len(run_times)
        avg_num_groups = sum(run_num_groups) / len(run_num_groups)
        avg_groups_per_second = sum(run_groups_per_second) / len(run_groups_per_second)
        avg_group_size_overall = sum(run_avg_group_size) / len(run_avg_group_size)
        avg_stability_overall = sum(run_avg_stability) / len(run_avg_stability)
        
        # Виводимо результати
        print(f"  Середній час виконання: {avg_execution_time:.2f} секунд")
        print(f"  Середня кількість груп: {avg_num_groups:.2f}")
        print(f"  Середня кількість груп за секунду: {avg_groups_per_second:.2f}")
        print(f"  Середній розмір групи: {avg_group_size_overall:.2f}")
        print(f"  Середня стабільність груп: {avg_stability_overall:.2f}%")
        
        # Зберігаємо результати
        results['num_services'].append(num_services)
        results['execution_time'].append(avg_execution_time)
        results['num_groups'].append(avg_num_groups)
        results['groups_per_second'].append(avg_groups_per_second)
        results['avg_group_size'].append(avg_group_size_overall)
        results['avg_stability'].append(avg_stability_overall)
    
    return results

def plot_results(results):
    """
    Візуалізує результати тестів продуктивності.
    
    Args:
        results: Словник з результатами тестів
    """
    # Створюємо фігуру з кількома графіками
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    
    # Графік часу виконання
    axs[0, 0].plot(results['num_services'], results['execution_time'], 'o-', color='blue')
    axs[0, 0].set_title('Час виконання')
    axs[0, 0].set_xlabel('Кількість мікросервісів')
    axs[0, 0].set_ylabel('Час (секунди)')
    axs[0, 0].grid(True)
    
    # Графік кількості груп
    axs[0, 1].plot(results['num_services'], results['num_groups'], 'o-', color='green')
    axs[0, 1].set_title('Кількість груп')
    axs[0, 1].set_xlabel('Кількість мікросервісів')
    axs[0, 1].set_ylabel('Кількість груп')
    axs[0, 1].grid(True)
    
    # Графік груп за секунду
    axs[1, 0].plot(results['num_services'], results['groups_per_second'], 'o-', color='red')
    axs[1, 0].set_title('Груп за секунду')
    axs[1, 0].set_xlabel('Кількість мікросервісів')
    axs[1, 0].set_ylabel('Груп/секунду')
    axs[1, 0].grid(True)
    
    # Графік середнього розміру групи
    axs[1, 1].plot(results['num_services'], results['avg_group_size'], 'o-', color='purple')
    axs[1, 1].set_title('Середній розмір групи')
    axs[1, 1].set_xlabel('Кількість мікросервісів')
    axs[1, 1].set_ylabel('Середній розмір')
    axs[1, 1].grid(True)
    
    plt.tight_layout()
    plt.savefig('performance_results.png')
    plt.show()

if __name__ == "__main__":
    # Налаштування тесту
    num_services_list = [10, 50, 100, 200, 500]
    time_slots = 20
    max_group_size = 4
    stability_threshold = 20.0
    pattern_distribution = {'stable': 0.25, 'peak': 0.4, 'complementary': 0.25, 'random': 0.1}
    num_runs = 3
    
    # Запускаємо тест
    results = run_performance_test(
        num_services_list, 
        time_slots, 
        max_group_size, 
        stability_threshold, 
        pattern_distribution, 
        num_runs
    )
    
    # Візуалізуємо результати
    plot_results(results)
    
    # Зберігаємо результати в файл
    with open('performance_results.txt', 'w') as f:
        f.write("=== РЕЗУЛЬТАТИ ТЕСТУ ПРОДУКТИВНОСТІ ===\n")
        f.write(f"Кількість таймслотів: {time_slots}\n")
        f.write(f"Максимальний розмір групи: {max_group_size}\n")
        f.write(f"Поріг стабільності: {stability_threshold}%\n")
        f.write(f"Розподіл патернів: {pattern_distribution}\n")
        f.write(f"Кількість запусків для кожної конфігурації: {num_runs}\n\n")
        
        f.write("| Кількість мікросервісів | Час виконання (с) | Кількість груп | Груп/секунду | Середній розмір групи | Середня стабільність (%) |\n")
        f.write("|--------------------------|-------------------|----------------|--------------|------------------------|---------------------------|\n")
        
        for i in range(len(results['num_services'])):
            f.write(f"| {results['num_services'][i]:24} | {results['execution_time'][i]:17.2f} | {results['num_groups'][i]:14.2f} | {results['groups_per_second'][i]:12.2f} | {results['avg_group_size'][i]:22.2f} | {results['avg_stability'][i]:25.2f} |\n") 