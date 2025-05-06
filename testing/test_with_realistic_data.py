import sys
import os

# Додаємо кореневу директорію проекту до шляху пошуку модулів
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from testing import realistic_data_generator as rdg
import json

def test_realistic_workload(num_services=50, generate_new_data=True, input_file="testing/realistic_data.json"):
    """
    Тестує алгоритм на реалістичних даних мікросервісів з 24 часовими слотами
    
    Args:
        num_services: Кількість мікросервісів для генерації
        generate_new_data: Якщо True, генерує нові дані, інакше завантажує з файлу
        input_file: Файл для збереження/завантаження даних
    """
    print("\n" + "="*80)
    print("ТЕСТУВАННЯ НА РЕАЛІСТИЧНИХ ДАНИХ З 24 ЧАСОВИМИ СЛОТАМИ")
    print("="*80)
    
    if generate_new_data:
        # Генеруємо набір мікросервісів
        print(f"Генерація {num_services} мікросервісів з реалістичними добовими патернами навантаження...")
        services = rdg.generate_microservice_dataset(num_services, input_file)
        print(f"Дані згенеровано і збережено у файл '{input_file}'")
    else:
        # Завантажуємо існуючі дані
        print(f"Завантаження даних з файлу '{input_file}'...")
        try:
            with open(input_file, 'r') as f:
                services = json.load(f)
            print(f"Завантажено {len(services)} мікросервісів")
        except Exception as e:
            print(f"Помилка при завантаженні даних: {e}")
            print("Генерація нових даних...")
            services = rdg.generate_microservice_dataset(num_services, input_file)
            print(f"Дані згенеровано і збережено у файл '{input_file}'")
    
    # Тестуємо алгоритм
    print("\nЗапуск алгоритму формування стабільних груп...")
    groups, group_services, slot_sums = main.form_stable_groups(services)
    
    # Аналіз результатів
    print("\nРезультати групування:")
    print(f"Кількість створених груп: {len(groups)}")
    
    # Обчислюємо статистики для кожної групи
    group_stats = []
    for i, (group, service_indices, sums) in enumerate(zip(groups, group_services, slot_sums)):
        mean = sum(sums) / len(sums)
        variance = sum((x - mean) ** 2 for x in sums) / len(sums)
        std_dev = variance ** 0.5
        cv = (std_dev / mean) * 100 if mean > 0 else float('inf')
        
        group_stats.append({
            'group_id': i,
            'size': len(service_indices),
            'mean': mean,
            'std_dev': std_dev,
            'cv': cv,
            'services': service_indices
        })
    
    # Сортуємо групи за коефіцієнтом варіації
    group_stats.sort(key=lambda x: x['cv'])
    
    # Виводимо статистику
    print("\nСтатистика груп (відсортована за коефіцієнтом варіації):")
    print(f"{'ID групи':<10} {'Розмір':<10} {'Сер. навант.':<15} {'Станд. відх.':<15} {'Коеф. варіації':<15}")
    print("-" * 65)
    
    for stat in group_stats:
        print(f"{stat['group_id']:<10} {stat['size']:<10} {stat['mean']:.2f}{' '*11} {stat['std_dev']:.2f}{' '*11} {stat['cv']:.2f}%")
    
    # Загальна статистика
    all_cvs = [stat['cv'] for stat in group_stats]
    avg_cv = sum(all_cvs) / len(all_cvs) if all_cvs else 0
    min_cv = min(all_cvs) if all_cvs else 0
    max_cv = max(all_cvs) if all_cvs else 0
    
    # Аналіз розмірів груп
    group_sizes = [stat['size'] for stat in group_stats]
    avg_size = sum(group_sizes) / len(group_sizes) if group_sizes else 0
    min_size = min(group_sizes) if group_sizes else 0
    max_size = max(group_sizes) if group_sizes else 0
    
    print("\nЗагальна статистика:")
    print(f"Кількість мікросервісів: {len(services)}")
    print(f"Кількість груп: {len(groups)}")
    print(f"Середній розмір групи: {avg_size:.2f} мікросервісів")
    print(f"Мін. розмір групи: {min_size}, Макс. розмір групи: {max_size}")
    print(f"Середній коефіцієнт варіації: {avg_cv:.2f}%")
    print(f"Мінімальний коефіцієнт варіації: {min_cv:.2f}%")
    print(f"Максимальний коефіцієнт варіації: {max_cv:.2f}%")
    
    # Кількість "ідеальних" груп (з коеф. варіації < 5%)
    ideal_groups = len([cv for cv in all_cvs if cv < 5])
    print(f"Кількість 'ідеальних' груп (CV < 5%): {ideal_groups} ({ideal_groups/len(groups)*100:.1f}%)")
    
    # Кількість "хороших" груп (з коеф. варіації < 10%)
    good_groups = len([cv for cv in all_cvs if cv < 10])
    print(f"Кількість 'хороших' груп (CV < 10%): {good_groups} ({good_groups/len(groups)*100:.1f}%)")
    
    # Аналіз найкращої і найгіршої групи
    best_group = group_stats[0]
    worst_group = group_stats[-1]
    
    print("\nНайкраща група:")
    print(f"ID: {best_group['group_id']}, Розмір: {best_group['size']}, CV: {best_group['cv']:.2f}%")
    
    print("\nНайгірша група:")
    print(f"ID: {worst_group['group_id']}, Розмір: {worst_group['size']}, CV: {worst_group['cv']:.2f}%")
    
    # Візуалізуємо результати
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Візуалізація коефіцієнтів варіації груп
        plt.figure(figsize=(12, 6))
        plt.bar(range(len(all_cvs)), all_cvs)
        plt.axhline(y=avg_cv, color='r', linestyle='-', label=f'Середнє: {avg_cv:.2f}%')
        plt.xlabel('Індекс групи')
        plt.ylabel('Коефіцієнт варіації (%)')
        plt.title('Коефіцієнти варіації груп')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.savefig('testing/group_variation_coefficients.png')
        print("\nГрафік коефіцієнтів варіації збережено у файл 'testing/group_variation_coefficients.png'")
        
        # Візуалізація найкращої групи
        best_group_id = best_group['group_id']
        plt.figure(figsize=(12, 6))
        
        # Візуалізуємо навантаження кожного мікросервісу в групі
        hours = list(range(24))
        for i, service_idx in enumerate(group_services[best_group_id]):
            plt.plot(hours, services[service_idx], 'o-', alpha=0.7, label=f'Мікросервіс {service_idx}')
        
        # Візуалізуємо сумарне навантаження групи
        plt.plot(hours, slot_sums[best_group_id], 'r--', linewidth=2, label='Сумарне навантаження')
        
        plt.xlabel('Година доби')
        plt.ylabel('Навантаження')
        plt.title(f'Найкраща група (ID: {best_group_id}, CV: {best_group["cv"]:.2f}%)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(range(0, 24, 2))
        plt.legend()
        plt.savefig('testing/best_group_load.png')
        print("Графік навантаження найкращої групи збережено у файл 'testing/best_group_load.png'")
        
        # Візуалізація найгіршої групи
        worst_group_id = worst_group['group_id']
        plt.figure(figsize=(12, 6))
        
        # Візуалізуємо навантаження кожного мікросервісу в групі
        for i, service_idx in enumerate(group_services[worst_group_id]):
            plt.plot(hours, services[service_idx], 'o-', alpha=0.7, label=f'Мікросервіс {service_idx}')
        
        # Візуалізуємо сумарне навантаження групи
        plt.plot(hours, slot_sums[worst_group_id], 'r--', linewidth=2, label='Сумарне навантаження')
        
        plt.xlabel('Година доби')
        plt.ylabel('Навантаження')
        plt.title(f'Найгірша група (ID: {worst_group_id}, CV: {worst_group["cv"]:.2f}%)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(range(0, 24, 2))
        plt.legend()
        plt.savefig('testing/worst_group_load.png')
        print("Графік навантаження найгіршої групи збережено у файл 'testing/worst_group_load.png'")
        
    except ImportError:
        print("\nДля візуалізації потрібна бібліотека matplotlib")
    except Exception as e:
        print(f"\nПомилка при візуалізації: {e}")
    
    print("\nТестування завершено.")
    return groups, group_services, slot_sums

if __name__ == "__main__":
    # Запускаємо з існуючими даними (без генерації нових)
    test_realistic_workload(generate_new_data=True) 