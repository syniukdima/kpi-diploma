def calculate_stability(group):
    """
    Calculates the coefficient of variation for a group of microservices.
    Lower value = better stability.
    
    Args:
        group: List of time series for microservice loads in the group
        
    Returns:
        Coefficient of variation in percentage
    """
    # Calculate the sum for each time slot
    time_slots = len(group[0])
    slot_sums = [0] * time_slots
    
    for service in group:
        for t in range(time_slots):
            slot_sums[t] += service[t]
    
    # Calculate the coefficient of variation
    mean = sum(slot_sums) / len(slot_sums)
    
    if mean == 0:
        return float('inf')
    
    variance = sum((x - mean) ** 2 for x in slot_sums) / len(slot_sums)
    std_dev = variance ** 0.5
    
    return (std_dev / mean) * 100  # Coefficient of variation in percentage

def calculate_load_sum(services):
    """
    Calculates the total load of each time slot for a set of microservices.
    
    Args:
        services: List of time series for microservice loads
        
    Returns:
        List of total loads by time slots
    """
    if not services:
        return []
    
    time_slots = len(services[0])
    slot_sums = [0] * time_slots
    
    for service in services:
        for t in range(time_slots):
            slot_sums[t] += service[t]
    
    return slot_sums

def generate_stable_groups(available_indices, microservices, group_size, stability_threshold):
    """
    Generates all possible combinations of the given size from available microservices,
    filters by stability threshold, and sorts by CV (ascending).
    
    Args:
        available_indices: List of available microservice indices
        microservices: List of all microservices
        group_size: Size of groups to generate
        stability_threshold: Maximum CV value to consider stable
    
    Returns:
        List of tuples (group, indices, cv) sorted by cv ascending
    """
    from itertools import combinations
    
    candidate_groups = []
    
    # Generate all combinations of current group size from available microservices
    for indices in combinations(range(len(available_indices)), group_size):
        # Map to actual microservice indices
        actual_indices = [available_indices[i] for i in indices]
        # Get the microservices for these indices
        group = [microservices[idx] for idx in actual_indices]
        
        # Calculate stability for this group
        cv = calculate_stability(group)
        
        # If stability is good enough, add to candidates
        if cv < stability_threshold:
            candidate_groups.append((group, actual_indices, cv))
    
    # Sort candidate groups by stability (lowest CV first)
    return sorted(candidate_groups, key=lambda x: x[2])

def is_group_available(group_indices, used_indices_set):
    """
    Checks if all indices in the group are still available (not used).
    
    Args:
        group_indices: List of indices to check
        used_indices_set: Set of already used indices
        
    Returns:
        True if all indices are available, False otherwise
    """
    return not any(idx in used_indices_set for idx in group_indices)

def form_multiple_knapsack_groups(microservices, num_knapsacks=None, max_group_size=4, stability_threshold=20.0):
    """
    Формує групи мікросервісів з використанням інкрементального підходу та розділення піків:
    1. Спочатку намагається групувати по 2, зберігаючи пари з хорошою стабільністю
    2. Потім намагається групувати сервіси, що залишились, по 3, і так далі
    3. Для сервісів, які не вдалося згрупувати, розділяє їх на базовий та піковий компоненти
    4. Базові компоненти відправляє на повторний пошук груп
    5. Пікові компоненти додає як окремі групи в самому кінці
    
    Args:
        microservices: Список часових рядів з навантаженням мікросервісів
        num_knapsacks: Кількість груп для формування. Якщо None, визначається автоматично
        max_group_size: Максимальна кількість елементів у групі (за замовчуванням: 4)
        stability_threshold: Поріг для коефіцієнта варіації (за замовчуванням: 20.0%)
        
    Returns:
        Кортеж з (groups, group_services, slot_sums)
        - groups: Список груп, де кожна група містить часові ряди мікросервісів
        - group_services: Список індексів мікросервісів у кожній групі
        - slot_sums: Список загальних навантажень за часовими слотами для кожної групи
    """
    from split_extreme_loads import process_unassigned_microservices
    
    n = len(microservices)
    
    # Ініціалізуємо фінальні групи
    final_groups = []
    final_group_indices = []
    final_slot_sums = []
    
    # Зберігаємо пікові компоненти для додавання в кінці
    peak_components = []
    peak_indices = []
    peak_slot_sums = []
    
    # Відстежуємо, які мікросервіси ще доступні
    available_indices = list(range(n))
    
    # Перший прохід: спробуємо згрупувати оригінальні мікросервіси
    available_indices = group_original_microservices(
        microservices, 
        available_indices, 
        max_group_size, 
        stability_threshold, 
        final_groups, 
        final_group_indices, 
        final_slot_sums
    )
    
    # Якщо є мікросервіси, які не вдалося згрупувати
    if not available_indices:
        return finalize_results(final_groups, final_group_indices, final_slot_sums, 
                               peak_components, peak_indices, peak_slot_sums)
    
    # Розділяємо незгруповані мікросервіси на базові та пікові компоненти
    print(f"\nРозділення {len(available_indices)} незгрупованих мікросервісів на базові та пікові компоненти")
    (base_services, base_indices), (peak_services, peak_indices_orig) = process_unassigned_microservices(
        available_indices, microservices
    )
    
    # Зберігаємо пікові компоненти для додавання в кінці
    process_peak_components(peak_services, peak_indices_orig, peak_components, peak_indices, peak_slot_sums)
    
    # Другий прохід: спробуємо згрупувати базові компоненти
    if base_services:
        process_base_components(
            base_services, 
            base_indices, 
            max_group_size, 
            stability_threshold,
            final_groups, 
            final_group_indices, 
            final_slot_sums
        )
    
    # Якщо ми не сформували жодної групи, розміщуємо кожен мікросервіс у свою групу
    if not final_groups:
        print("Жодної групи не сформовано. Створюємо групи з одного елемента.")
        final_groups = [[microservice] for microservice in microservices]
        final_group_indices = [[i] for i in range(n)]
        final_slot_sums = [calculate_load_sum([microservice]) for microservice in microservices]
    
    return finalize_results(final_groups, final_group_indices, final_slot_sums, 
                           peak_components, peak_indices, peak_slot_sums)


def group_original_microservices(microservices, available_indices, max_group_size, stability_threshold, 
                                final_groups, final_group_indices, final_slot_sums):
    """
    Групує оригінальні мікросервіси, перебираючи різні розміри груп
    
    Args:
        microservices: Список часових рядів з навантаженням мікросервісів
        available_indices: Список доступних індексів мікросервісів
        max_group_size: Максимальна кількість елементів у групі
        stability_threshold: Поріг для коефіцієнта варіації
        final_groups: Список груп для доповнення
        final_group_indices: Список індексів мікросервісів у кожній групі
        final_slot_sums: Список загальних навантажень за часовими слотами для кожної групи
        
    Returns:
        Оновлений список доступних індексів
    """
    n = len(microservices)
    
    # Ітеруємо за розмірами груп від 2 до max_group_size
    for group_size in range(2, min(max_group_size + 1, n + 1)):
        print(f"\nПробуємо розмір групи: {group_size}")
        
        if len(available_indices) < group_size:
            print(f"  Недостатньо сервісів залишилось для розміру групи {group_size}")
            break
        
        # Генеруємо стабільні групи для поточного розміру
        candidate_groups = generate_stable_groups(
            available_indices, 
            microservices, 
            group_size, 
            stability_threshold
        )
        
        if not candidate_groups:
            print(f"  Не знайдено стабільних груп розміром {group_size}")
            continue
        
        print(f"  Знайдено {len(candidate_groups)} стабільних груп розміром {group_size}")
        
        # Створюємо набір всіх вже використаних індексів для швидкого пошуку
        used_indices_set = set(idx for group in final_group_indices for idx in group)
        
        # Додаємо стабільні групи до фінальних груп
        for group, actual_indices, cv in candidate_groups:
            # Пропускаємо, якщо будь-який індекс вже використовується
            if not is_group_available(actual_indices, used_indices_set):
                continue
                
            # Додаємо цю групу до фінальних груп
            final_groups.append(group)
            final_group_indices.append(actual_indices)
            final_slot_sums.append(calculate_load_sum(group))
            
            # Оновлюємо набір використаних індексів
            used_indices_set.update(actual_indices)
            
            print(f"  Додано групу з CV: {cv:.2f}% - {actual_indices}")
        
        # Оновлюємо доступні індекси, видаляючи використані
        available_indices = [idx for idx in available_indices if idx not in used_indices_set]
        
        print(f"  Залишилось сервісів: {len(available_indices)}")
        
        # Якщо не залишилось мікросервісів, завершуємо
        if not available_indices:
            break
    
    return available_indices


def process_peak_components(peak_services, peak_indices_orig, peak_components, peak_indices, peak_slot_sums):
    """
    Обробляє пікові компоненти і зберігає їх для додавання в кінці
    
    Args:
        peak_services: Список часових рядів пікових компонентів
        peak_indices_orig: Список індексів вихідних мікросервісів
        peak_components: Список для збереження пікових компонентів
        peak_indices: Список для збереження індексів пікових компонентів
        peak_slot_sums: Список для збереження сум навантажень пікових компонентів
    """
    print("\nЗберігаємо пікові компоненти для додавання в кінці:")
    for i, (service, idx) in enumerate(zip(peak_services, peak_indices_orig)):
        peak_components.append([service])
        # Використовуємо від'ємні індекси для позначення пікових компонентів
        peak_indices.append([-idx])
        peak_slot_sums.append(calculate_load_sum([service]))
        print(f"  Збережено піковий компонент мікросервісу: {idx}")


def process_base_components(base_services, base_indices, max_group_size, stability_threshold,
                          final_groups, final_group_indices, final_slot_sums):
    """
    Обробляє базові компоненти, групуючи їх і додаючи до фінальних результатів
    
    Args:
        base_services: Список часових рядів базових компонентів
        base_indices: Список індексів вихідних мікросервісів
        max_group_size: Максимальна кількість елементів у групі
        stability_threshold: Поріг для коефіцієнта варіації
        final_groups: Список груп для доповнення
        final_group_indices: Список індексів мікросервісів у кожній групі
        final_slot_sums: Список загальних навантажень за часовими слотами для кожної групи
    """
    print(f"\nДругий прохід алгоритму для {len(base_services)} базових компонентів")
    
    # Створюємо тимчасові структури для другого проходу
    temp_groups = []
    temp_indices = []
    temp_slots = []
    
    # Доступні базові компоненти для другого проходу
    base_available = list(range(len(base_services)))
    
    # Групуємо базові компоненти
    base_available = group_base_components(
        base_services, 
        base_indices, 
        base_available, 
        max_group_size, 
        stability_threshold, 
        temp_groups, 
        temp_indices, 
        temp_slots
    )
    
    # Додаємо до фінальних результатів сформовані групи базових компонентів
    for i, (group, indices, slots) in enumerate(zip(temp_groups, temp_indices, temp_slots)):
        # Перетворюємо індекси базових компонентів на оригінальні індекси мікросервісів
        real_indices = [base_indices[idx] for idx in indices]
        
        final_groups.append(group)
        # Додаємо префікс 1000 до індексів, щоб відрізняти базові компоненти від оригінальних мікросервісів
        final_group_indices.append([1000 + idx for idx in real_indices])
        final_slot_sums.append(slots)
    
    # Додаємо базові компоненти, які не вдалося згрупувати, як окремі групи
    add_ungrouped_base_components(
        base_services, 
        base_indices, 
        base_available, 
        final_groups, 
        final_group_indices, 
        final_slot_sums
    )


def group_base_components(base_services, base_indices, base_available, max_group_size, stability_threshold,
                         temp_groups, temp_indices, temp_slots):
    """
    Групує базові компоненти
    
    Args:
        base_services: Список часових рядів базових компонентів
        base_indices: Список індексів вихідних мікросервісів
        base_available: Список доступних індексів базових компонентів
        max_group_size: Максимальна кількість елементів у групі
        stability_threshold: Поріг для коефіцієнта варіації
        temp_groups: Список тимчасових груп для доповнення
        temp_indices: Список тимчасових індексів для доповнення
        temp_slots: Список тимчасових сум навантажень для доповнення
        
    Returns:
        Оновлений список доступних індексів базових компонентів
    """
    # Повторюємо цикл для базових компонентів
    for group_size in range(2, min(max_group_size + 1, len(base_services) + 1)):
        print(f"\nПробуємо розмір групи для базових компонентів: {group_size}")
        
        if len(base_available) < group_size:
            print(f"  Недостатньо базових компонентів для розміру групи {group_size}")
            break
        
        # Генеруємо стабільні групи базових компонентів
        candidate_groups = generate_stable_groups(
            base_available, 
            base_services, 
            group_size, 
            stability_threshold
        )
        
        if not candidate_groups:
            print(f"  Не знайдено стабільних груп розміром {group_size}")
            continue
        
        print(f"  Знайдено {len(candidate_groups)} стабільних груп розміром {group_size}")
        
        # Створюємо набір всіх вже використаних індексів для швидкого пошуку
        used_base_set = set(idx for group in temp_indices for idx in group)
        
        # Додаємо стабільні групи до тимчасових груп
        for group, actual_indices, cv in candidate_groups:
            # Пропускаємо, якщо будь-який індекс вже використовується
            if not is_group_available(actual_indices, used_base_set):
                continue
                
            # Додаємо цю групу до тимчасових груп
            temp_groups.append(group)
            temp_indices.append(actual_indices)
            temp_slots.append(calculate_load_sum(group))
            
            # Оновлюємо набір використаних індексів
            used_base_set.update(actual_indices)
            
            # Виводимо індекси оригінальних мікросервісів для зрозумілості
            real_indices = [base_indices[idx] for idx in actual_indices]
            print(f"  Додано групу базових компонентів з CV: {cv:.2f}% - оригінальні індекси: {real_indices}")
        
        # Оновлюємо доступні базові компоненти
        base_available = [idx for idx in base_available if idx not in used_base_set]
        
        print(f"  Залишилось базових компонентів: {len(base_available)}")
        
        # Якщо не залишилось базових компонентів, завершуємо
        if not base_available:
            break
    
    return base_available


def add_ungrouped_base_components(base_services, base_indices, base_available,
                                final_groups, final_group_indices, final_slot_sums):
    """
    Додає незгруповані базові компоненти як окремі групи
    
    Args:
        base_services: Список часових рядів базових компонентів
        base_indices: Список індексів вихідних мікросервісів
        base_available: Список доступних індексів базових компонентів
        final_groups: Список груп для доповнення
        final_group_indices: Список індексів мікросервісів у кожній групі
        final_slot_sums: Список загальних навантажень за часовими слотами для кожної групи
    """
    print("\nДодаємо незгруповані базові компоненти як окремі групи:")
    for idx in base_available:
        service = base_services[idx]
        real_idx = base_indices[idx]
        
        final_groups.append([service])
        # Використовуємо префікс 1000 для базових компонентів
        final_group_indices.append([1000 + real_idx])
        final_slot_sums.append(calculate_load_sum([service]))
        print(f"  Додано базовий компонент мікросервісу: {real_idx}")


def finalize_results(final_groups, final_group_indices, final_slot_sums,
                   peak_components, peak_indices, peak_slot_sums):
    """
    Формує фінальні результати, додаючи пікові компоненти в кінці
    
    Args:
        final_groups: Список груп
        final_group_indices: Список індексів мікросервісів у кожній групі
        final_slot_sums: Список загальних навантажень за часовими слотами для кожної групи
        peak_components: Список пікових компонентів
        peak_indices: Список індексів пікових компонентів
        peak_slot_sums: Список сум навантажень пікових компонентів
        
    Returns:
        Кортеж з (groups, group_services, slot_sums)
    """
    # Додаємо пікові компоненти в самому кінці
    if peak_components:
        print("\nДодаємо пікові компоненти як окремі групи в самому кінці:")
        for i, (group, indices, slots) in enumerate(zip(peak_components, peak_indices, peak_slot_sums)):
            final_groups.append(group)
            final_group_indices.append(indices)
            final_slot_sums.append(slots)
            print(f"  Додано піковий компонент мікросервісу: {-indices[0]}")
    
    return final_groups, final_group_indices, final_slot_sums

def print_results(groups, group_services, slot_sums):
    """
    Prints the results of microservice grouping.
    
    Args:
        groups: List of groups, where each group contains time series of microservices
        group_services: List of microservice indices in each group
        slot_sums: List of total loads by time slots for each group
    """
    print("Grouping results:")
    
    for i, (group, service_indices, sums) in enumerate(zip(groups, group_services, slot_sums)):
        # Calculate statistics
        mean = sum(sums) / len(sums)
        variance = sum((x - mean) ** 2 for x in sums) / len(sums)
        std_dev = variance ** 0.5
        cv = (std_dev / mean) * 100 if mean > 0 else float('inf')
        
        print(f"\nGroup {i+1}:")
        print(f"  Microservices: {service_indices}")
        
        print("  Individual load by time slots:")
        for j, service in enumerate(group):
            print(f"    Microservice {service_indices[j]}: {service}")
        
        print(f"  Total load by time slots: {sums}")
        print(f"  Average load: {mean:.2f}")
        print(f"  Standard deviation: {std_dev:.2f}")
        print(f"  Coefficient of variation: {cv:.2f}%")
    
    # Calculate overall statistics
    print("\nOverall statistics:")
    print(f"  Number of groups: {len(groups)}")
    print(f"  Total number of microservices: {sum(len(g) for g in group_services)}")
    
    # Calculate average coefficient of variation for all groups
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
    
    print(f"  Average coefficient of variation: {avg_cv:.2f}%")

# Usage example
if __name__ == "__main__":
    # Example with more microservices (6 time slots)
    print("\n" + "="*60)
    print("Input data:")
    
    microservices = [
        [1, 2, 3, 4, 3, 2],  # Microservice 0
        [2, 1, 1, 2, 3, 4],  # Microservice 1
        [3, 3, 2, 1, 2, 3],  # Microservice 2
        [4, 3, 2, 1, 1, 2],  # Microservice 3
        [2, 3, 4, 3, 2, 1],  # Microservice 4
        [1, 2, 3, 4, 4, 3],  # Microservice 5
        [3, 2, 1, 2, 3, 4],  # Microservice 6
        [4, 3, 2, 1, 2, 3],  # Microservice 7
    ]
    
    for i, service in enumerate(microservices):
        print(f"Microservice {i}: {service}")
    print("="*60 + "\n")
    
    try:
        # Set max_group_size to try different group sizes
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices, 
            num_knapsacks=3,
            max_group_size=4
        )
        print_results(groups, group_services, slot_sums)
    except ValueError as e:
        print(f"Error: {e}")
    
    

