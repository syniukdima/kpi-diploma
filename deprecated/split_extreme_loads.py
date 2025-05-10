import numpy as np

def split_microservice_load(time_series, threshold_std=0.1):
    """
    Розділяє навантаження мікросервісу на базову та пікову складову.
    
    Алгоритм:
    1. Знаходить пікові значення, які перевищують середнє + threshold_std * стандартне_відхилення
    2. Розширює область піків, включаючи суміжні значення, що перевищують середнє
    3. Розділяє часовий ряд на дві компоненти:
       - базову (обмежену максимальним непіковим значенням)
       - пікову (надлишкове навантаження)
    
    Args:
        time_series: Часовий ряд навантаження мікросервісу
        threshold_std: Поріг у стандартних відхиленнях для визначення піків (за замовчуванням 0.1)
    
    Returns:
        Кортеж з двох списків: (базове_навантаження, пікове_навантаження)
    """
    # Перетворення в numpy array, якщо це не array
    time_series = np.array(time_series)
    
    # Обчислюємо середнє та стандартне відхилення
    mean = np.mean(time_series)
    std_dev = np.std(time_series)
    
    # Визначаємо екстремуми (аномалії)
    extremes = time_series[(time_series > mean + threshold_std * std_dev)]
    
    # Якщо екстремумів немає, повертаємо оригінальний ряд та нульовий ряд
    if len(extremes) == 0:
        return time_series.tolist(), [0] * len(time_series)
    
    # Знаходимо індекси екстремумів
    extreme_indices = np.where(time_series > mean + threshold_std * std_dev)[0]
    
    # Знаходимо індекси першого та останнього екстремуму
    first_idx = extreme_indices[0]
    last_idx = extreme_indices[-1]
    
    # Розширюємо область екстремумів ліворуч
    extremes_extension_left = []
    extreme_indices_left = []
    for i in range(first_idx - 1, -1, -1):
        if time_series[i] > mean:
            extremes_extension_left.append(time_series[i])
            extreme_indices_left.append(i)
        else:
            break
    
    # Розширюємо область екстремумів праворуч
    extremes_extension_right = []
    extreme_indices_right = []
    for i in range(last_idx + 1, len(time_series)):
        if time_series[i] > mean:
            extremes_extension_right.append(time_series[i])
            extreme_indices_right.append(i)
        else:
            break
    
    # Об'єднуємо всі індекси екстремумів та розширення
    all_extreme_indices = sorted(extreme_indices_left + extreme_indices.tolist() + extreme_indices_right)
    
    # Створюємо маску для значень, які не входять в розширену область екстремумів
    mask = np.ones(len(time_series), dtype=bool)
    mask[all_extreme_indices] = False
    
    # Знаходимо максимальне значення за виключенням екстремумів
    # Це буде порогом для "базового" навантаження
    if np.any(mask):
        new_max_value = np.max(time_series[mask])
    else:
        # Якщо всі значення є екстремумами, використовуємо середнє значення
        new_max_value = mean
    
    # Створюємо базовий ряд (обмежений новим максимумом)
    base_load = np.minimum(time_series, new_max_value)
    
    # Створюємо піковий ряд (надлишок над новим максимумом)
    peak_load = np.maximum(time_series - new_max_value, 0)
    
    return base_load.tolist(), peak_load.tolist()

def process_unassigned_microservices(unassigned_indices, microservices):
    """
    Обробляє мікросервіси, які не вдалося згрупувати, 
    розділяючи їх на базові та пікові компоненти.
    
    Args:
        unassigned_indices: Індекси мікросервісів, які не вдалося згрупувати
        microservices: Список усіх мікросервісів
    
    Returns:
        Кортеж з двох списків: 
        (списки базових компонентів з індексами, списки пікових компонентів з індексами)
    """
    base_services = []
    base_indices = []
    peak_services = []
    peak_indices = []
    
    for idx in unassigned_indices:
        microservice = microservices[idx]
        base_load, peak_load = split_microservice_load(microservice)
        
        # Додаємо базовий компонент зі збереженням індексу
        base_services.append(base_load)
        base_indices.append(idx)
        
        # Додаємо піковий компонент, лише якщо він містить ненульові значення
        if any(x > 0 for x in peak_load):
            peak_services.append(peak_load)
            peak_indices.append(idx)
    
    return (base_services, base_indices), (peak_services, peak_indices) 