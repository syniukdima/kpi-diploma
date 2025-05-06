def calculate_stability(group):
    """
    Обчислює коефіцієнт варіації для групи мікросервісів.
    Менше значення = краща стабільність.
    
    Args:
        group: Список часових рядів навантаження мікросервісів у групі
        
    Returns:
        Коефіцієнт варіації у відсотках
    """
    # Обчислюємо суму для кожного часового слоту
    time_slots = len(group[0])
    slot_sums = [0] * time_slots
    
    for service in group:
        for t in range(time_slots):
            slot_sums[t] += service[t]
    
    # Обчислюємо коефіцієнт варіації
    mean = sum(slot_sums) / len(slot_sums)
    
    if mean == 0:
        return float('inf')
    
    variance = sum((x - mean) ** 2 for x in slot_sums) / len(slot_sums)
    std_dev = variance ** 0.5
    
    return (std_dev / mean) * 100  # Коефіцієнт варіації у відсотках

def calculate_load_sum(services):
    """
    Обчислює сумарне навантаження кожного часового слоту для набору мікросервісів.
    
    Args:
        services: Список часових рядів навантаження мікросервісів
        
    Returns:
        Список сумарного навантаження по часових слотах
    """
    if not services:
        return []
    
    time_slots = len(services[0])
    slot_sums = [0] * time_slots
    
    for service in services:
        for t in range(time_slots):
            slot_sums[t] += service[t]
    
    return slot_sums

def form_stable_groups(microservices):
    """
    Формує групи мікросервісів використовуючи алгоритм упакування множинного рюкзака
    з гнучким обмеженням цільової ваги.
    
    Args:
        microservices: Список часових рядів навантаження мікросервісів
    
    Returns:
        Tuple of (groups, group_services, slot_sums)
        - groups: Список груп, де кожна група містить часові ряди мікросервісів
        - group_services: Список індексів мікросервісів у кожній групі
        - slot_sums: Список сумарного навантаження по часових слотах для кожної групи
    """
    n = len(microservices)
    time_slots = len(microservices[0])
    
    # Підготовка даних для рюкзака
    service_indices = list(range(n))
    
    # Обчислюємо ідеальне цільове навантаження - середнє по всіх мікросервісах
    total_load = [0] * time_slots
    for service in microservices:
        for t in range(time_slots):
            total_load[t] += service[t]
    
    avg_load_per_slot = sum(total_load) / (time_slots * n)
    
    # Алгоритм рюкзака з гнучким обмеженням
    groups = []  # Часові ряди мікросервісів у кожній групі
    group_services = []  # Індекси мікросервісів у кожній групі
    used = [False] * n
    slot_sums_per_group = []
    
    # Поки не всі мікросервіси розподілені
    while not all(used):
        # Ініціалізуємо нову групу
        current_group = []
        current_services = []
        current_load = [0] * time_slots
        
        # Шукаємо найкращий мікросервіс для початку нової групи
        best_start_idx = -1
        best_start_stability = float('inf')
        
        for i in range(n):
            if not used[i]:
                test_stability = calculate_stability([microservices[i]])
                if test_stability < best_start_stability:
                    best_start_stability = test_stability
                    best_start_idx = i
        
        # Додаємо найкращий початковий мікросервіс
        if best_start_idx != -1:
            current_group.append(microservices[best_start_idx])
            current_services.append(best_start_idx)
            used[best_start_idx] = True
            
            # Оновлюємо поточне навантаження групи
            for t in range(time_slots):
                current_load[t] += microservices[best_start_idx][t]
        
        # Намагаємось додати інші мікросервіси для досягнення цільового навантаження
        improved = True
        while improved:
            improved = False
            
            best_service_idx = -1
            best_stability = calculate_stability(current_group)
            
            # Цільове навантаження - це середнє навантаження всіх мікросервісів, помножене на поточний розмір групи
            target_load = avg_load_per_slot * (len(current_services) + 1)
            
            # Перебираємо всі невикористані мікросервіси
            for i in range(n):
                if not used[i]:
                    # Додаємо мікросервіс тимчасово
                    test_group = current_group + [microservices[i]]
                    
                    # Обчислюємо нову стабільність
                    test_stability = calculate_stability(test_group)
                    
                    # Якщо стабільність покращується, зберігаємо цей мікросервіс
                    if test_stability < best_stability:
                        best_stability = test_stability
                        best_service_idx = i
            
            # Якщо знайдено відповідний мікросервіс, додаємо його до групи
            if best_service_idx != -1:
                current_group.append(microservices[best_service_idx])
                current_services.append(best_service_idx)
                used[best_service_idx] = True
                
                # Оновлюємо поточне навантаження групи
                for t in range(time_slots):
                    current_load[t] += microservices[best_service_idx][t]
                
                improved = True
            
            # Якщо розмір групи досягнув максимуму або всі мікросервіси використані
            if len(current_services) >= n or all(used):
                break
        
        # Зберігаємо сформовану групу
        if current_group:
            groups.append(current_group)
            group_services.append(current_services)
            slot_sums_per_group.append(current_load)
    
    return groups, group_services, slot_sums_per_group

def print_results(groups, group_services, slot_sums):
    """
    Виводить результати групування мікросервісів.
    
    Args:
        groups: Список груп, де кожна група містить часові ряди мікросервісів
        group_services: Список індексів мікросервісів у кожній групі
        slot_sums: Список сумарного навантаження по часових слотах для кожної групи
    """
    print("Результати розподілу груп:")
    
    for i, (group, service_indices, sums) in enumerate(zip(groups, group_services, slot_sums)):
        # Обчислюємо статистики
        mean = sum(sums) / len(sums)
        variance = sum((x - mean) ** 2 for x in sums) / len(sums)
        std_dev = variance ** 0.5
        cv = (std_dev / mean) * 100 if mean > 0 else float('inf')
        
        print(f"\nГрупа {i+1}:")
        print(f"  Мікросервіси: {service_indices}")
        
        print("  Індивідуальне навантаження по часових слотах:")
        for j, service in enumerate(group):
            print(f"    Мікросервіс {service_indices[j]}: {service}")
        
        print(f"  Сумарне навантаження по часових слотах: {sums}")
        print(f"  Середнє навантаження: {mean:.2f}")
        print(f"  Стандартне відхилення: {std_dev:.2f}")
        print(f"  Коефіцієнт варіації: {cv:.2f}%")
    
    # Обчислюємо загальні статистики
    print("\nЗагальна статистика:")
    print(f"  Кількість груп: {len(groups)}")
    print(f"  Загальна кількість мікросервісів: {sum(len(g) for g in group_services)}")
    
    # Обчислюємо середній коефіцієнт варіації для всіх груп
    avg_cv = 0
    if groups:
        cvs = []
        for sums in slot_sums:
            mean = sum(sums) / len(sums)
            if mean > 0:
                variance = sum((x - mean) ** 2 for x in sums) / len(sums)
                std_dev = variance ** 0.5
                cvs.append((std_dev / mean) * 100)
        
        if cvs:
            avg_cv = sum(cvs) / len(cvs)
    
    print(f"  Середній коефіцієнт варіації: {avg_cv:.2f}%")

# Приклад використання
if __name__ == "__main__":
    # Приклад з мікросервісами (6 тайм слотів)
    print("\n" + "="*60)
    print("Вхідні дані:")
    
    microservices = [
        [1, 2, 3, 4, 3, 2],  # Мікросервіс 0
        [2, 1, 1, 2, 3, 4],  # Мікросервіс 1
        [3, 3, 2, 1, 2, 3],  # Мікросервіс 2
        [4, 3, 2, 1, 1, 2],  # Мікросервіс 3
        [2, 3, 4, 3, 2, 1],  # Мікросервіс 4
        [1, 2, 3, 4, 4, 3],  # Мікросервіс 5
        [3, 2, 1, 2, 3, 4],  # Мікросервіс 6
        [4, 3, 2, 1, 2, 3],  # Мікросервіс 7
    ]
    
    for i, service in enumerate(microservices):
        print(f"Мікросервіс {i}: {service}")
    print("="*60 + "\n")
    
    try:
        groups, group_services, slot_sums = form_stable_groups(microservices)
        print_results(groups, group_services, slot_sums)
    except ValueError as e:
        print(f"Помилка: {e}")
    
    

