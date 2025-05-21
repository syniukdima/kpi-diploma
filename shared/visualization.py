import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, Dict, Any
import json

class Visualizer:
    """
    Клас для візуалізації часових рядів мікросервісів та результатів групування
    """
    
    def __init__(self):
        """
        Ініціалізація візуалізатора
        """
        # Налаштування стилю графіків
        plt.style.use('ggplot')
        # Розмір графіків за замовчуванням
        self.figsize = (12, 6)
    
    def visualize_microservices(self, microservices: List[List[float]], 
                               service_names: List[str], 
                               title: str = "Часові ряди мікросервісів") -> None:
        """
        Візуалізація часових рядів мікросервісів
        
        Args:
            microservices: Список часових рядів мікросервісів
            service_names: Список назв мікросервісів
            title: Заголовок графіка
        """
        plt.figure(figsize=self.figsize)
        
        for i, (service, name) in enumerate(zip(microservices, service_names)):
            plt.plot(service, label=name, marker='o', linestyle='-', markersize=4)
        
        plt.title(title)
        plt.xlabel("Часовий слот")
        plt.ylabel("Навантаження")
        plt.legend(loc='best')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    def visualize_group_load(self, groups: List[List[List[float]]], 
                           group_services: List[List[int]], 
                           service_names: List[str],
                           title: str = "Загальне навантаження груп") -> None:
        """
        Візуалізація загального навантаження кожної групи
        
        Args:
            groups: Список груп, де кожна група містить часові ряди мікросервісів
            group_services: Список індексів мікросервісів у кожній групі
            service_names: Список назв мікросервісів
            title: Заголовок графіка
        """
        plt.figure(figsize=self.figsize)
        
        for i, group in enumerate(groups):
            # Обчислення загального навантаження групи
            time_slots = len(group[0]) if group else 0
            total_load = [0] * time_slots
            
            for service in group:
                for t in range(time_slots):
                    total_load[t] += service[t]
            
            # Побудова графіка для групи
            plt.plot(total_load, label=f"Група {i+1}", marker='o', linestyle='-', markersize=4)
        
        plt.title(title)
        plt.xlabel("Часовий слот")
        plt.ylabel("Загальне навантаження")
        plt.legend(loc='best')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    def visualize_stability_comparison(self, groups: List[List[List[float]]]) -> None:
        """
        Візуалізація порівняння стабільності груп
        
        Args:
            groups: Список груп, де кожна група містить часові ряди мікросервісів
        """
        plt.figure(figsize=self.figsize)
        
        cv_values = []
        group_labels = []
        
        for i, group in enumerate(groups):
            # Обчислення загального навантаження групи
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
        plt.show()
    
    def visualize_base_peak_components(self, 
                                     base_services: List[List[float]], 
                                     peak_services: List[List[float]],
                                     service_names: List[str]) -> None:
        """
        Візуалізація базових та пікових компонентів мікросервісів
        
        Args:
            base_services: Список часових рядів базових компонентів
            peak_services: Список часових рядів пікових компонентів
            service_names: Список назв мікросервісів
        """
        for i, (base, peak, name) in enumerate(zip(base_services, peak_services, service_names)):
            plt.figure(figsize=self.figsize)
            
            # Побудова графіків
            plt.plot(base, label="Базовий компонент", marker='o', linestyle='-', color='blue', markersize=4)
            plt.plot(peak, label="Піковий компонент", marker='x', linestyle='--', color='red', markersize=4)
            plt.plot([b + p for b, p in zip(base, peak)], label="Загальне навантаження", 
                    marker='s', linestyle='-.', color='green', markersize=4)
            
            plt.title(f"Розділення навантаження для мікросервісу: {name}")
            plt.xlabel("Часовий слот")
            plt.ylabel("Навантаження")
            plt.legend(loc='best')
            plt.grid(True)
            plt.tight_layout()
            plt.show()
    
    def visualize_group_statistics(self, groups: List[List[List[float]]], 
                                 group_services: List[List[int]],
                                 service_names: List[str]) -> None:
        """
        Візуалізація статистики по групах
        
        Args:
            groups: Список груп, де кожна група містить часові ряди мікросервісів
            group_services: Список індексів мікросервісів у кожній групі
            service_names: Список назв мікросервісів
        """
        # Підготовка даних для візуалізації
        group_sizes = [len(group) for group in group_services]
        
        # Обчислення середнього навантаження для кожної групи
        mean_loads = []
        peak_loads = []
        
        for group in groups:
            # Обчислення загального навантаження групи
            time_slots = len(group[0]) if group else 0
            total_load = [0] * time_slots
            
            for service in group:
                for t in range(time_slots):
                    total_load[t] += service[t]
            
            mean_loads.append(np.mean(total_load))
            peak_loads.append(max(total_load))
        
        # Створення фігури з декількома підграфіками
        fig, axs = plt.subplots(3, 1, figsize=(12, 12))
        
        # Розмір груп
        axs[0].bar(range(1, len(group_sizes) + 1), group_sizes)
        axs[0].set_title("Розмір груп")
        axs[0].set_xlabel("Номер групи")
        axs[0].set_ylabel("Кількість мікросервісів")
        axs[0].grid(True, axis='y')
        
        # Середнє навантаження
        axs[1].bar(range(1, len(mean_loads) + 1), mean_loads)
        axs[1].set_title("Середнє навантаження груп")
        axs[1].set_xlabel("Номер групи")
        axs[1].set_ylabel("Середнє навантаження")
        axs[1].grid(True, axis='y')
        
        # Пікове навантаження
        axs[2].bar(range(1, len(peak_loads) + 1), peak_loads)
        axs[2].set_title("Пікове навантаження груп")
        axs[2].set_xlabel("Номер групи")
        axs[2].set_ylabel("Пікове навантаження")
        axs[2].grid(True, axis='y')
        
        plt.tight_layout()
        plt.show()
        
        # Виведення текстової статистики
        print("\nСтатистика по групах:")
        print("-" * 50)
        for i, (size, mean, peak) in enumerate(zip(group_sizes, mean_loads, peak_loads)):
            print(f"Група {i+1}:")
            print(f"  Кількість мікросервісів: {size}")
            print(f"  Середнє навантаження: {mean:.2f}")
            print(f"  Пікове навантаження: {peak:.2f}")
            
            # Отримання списку мікросервісів у групі з урахуванням базових та пікових компонентів
            services_in_group = []
            for idx in group_services[i]:
                if idx >= 1000:  # Базовий компонент
                    real_idx = idx - 1000
                    if 0 <= real_idx < len(service_names):
                        services_in_group.append(f"{service_names[real_idx]} (базовий)")
                elif idx < 0:  # Піковий компонент
                    real_idx = -idx
                    if 0 <= real_idx < len(service_names):
                        services_in_group.append(f"{service_names[real_idx]} (піковий)")
                else:  # Звичайний мікросервіс
                    if 0 <= idx < len(service_names):
                        services_in_group.append(service_names[idx])
            
            print(f"  Мікросервіси: {services_in_group}")
            print("-" * 50)

# Приклад використання:
if __name__ == "__main__":
    from db_input import DBInput
    from group_finder import form_multiple_knapsack_groups
    
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
    
    # Візуалізація часових рядів мікросервісів
    visualizer.visualize_microservices(microservices, service_names)
    
    # Візуалізація загального навантаження груп
    visualizer.visualize_group_load(groups, group_services, service_names)
    
    # Візуалізація порівняння стабільності груп
    visualizer.visualize_stability_comparison(groups)
    
    # Візуалізація статистики по групах
    visualizer.visualize_group_statistics(groups, group_services, service_names) 