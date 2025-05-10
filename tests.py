import unittest
import numpy as np
from group_finder import calculate_stability, generate_stable_groups, form_multiple_knapsack_groups
import itertools

class TestMicroserviceGrouping(unittest.TestCase):
    def test_calculate_stability(self):
        # Тест 1: Ідеально стабільна група
        stable_group = [
            [1, 2, 3, 4],
            [4, 3, 2, 1]  # Сума завжди 5
        ]

        self.assertEqual(calculate_stability(stable_group), 0.0)

        # Тест 2: Нестабільна група
        unstable_group = [
            [1, 0, 1, 10],
            [10, 1, 0, 1]  # Великі коливання
        ]
        self.assertGreater(calculate_stability(unstable_group), 50.0)

        # Тест 3: Група з нульовим навантаженням
        zero_group = [
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.assertEqual(calculate_stability(zero_group), float('inf'))

        # Тест 4: Група з одним мікросервісом
        single_service = [[1, 2, 3, 4]]
        self.assertNotEqual(calculate_stability(single_service), 0.0)

    def test_form_multiple_knapsack_groups(self):
        # Тест 1: Простий випадок з чотирма мікросервісами
        microservices = [
            [1, 2, 3, 4],  # 0
            [4, 3, 2, 1],  # 1
            [2, 2, 2, 2],  # 2
            [3, 3, 3, 3]   # 3
        ]
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices, 
        )
        
        # Перевіряємо, що всі мікросервіси розподілені
        all_services = set()
        for service_group in group_services:
            all_services.update(service_group)
        self.assertEqual(all_services, set(range(len(microservices))))

        # Тест 2: Випадок з піковими навантаженнями
        peak_services = [
            [1, 1, 1, 10],  # Пік в кінці
            [1, 1, 1, 1],   # Стабільний
            [10, 1, 1, 1],  # Пік на початку
            [1, 1, 1, 1]    # Стабільний
        ]
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            peak_services,
        )
        
        # Перевіряємо, що всі мікросервіси розподілені
        all_services = set()
        for service_group in group_services:
            # Конвертуємо спеціальні індекси назад в оригінальні
            original_indices = []
            for idx in service_group:
                if idx < 0:  # Піковий компонент
                    original_indices.append(-idx)
                elif idx >= 1000:  # Базовий компонент
                    original_indices.append(idx - 1000)
                else:  # Оригінальний індекс
                    original_indices.append(idx)
            all_services.update(original_indices)
        self.assertEqual(all_services, set(range(len(peak_services))))

        # Тест 3
        large_services = [
            [1, 2, 3, 4],
            [4, 3, 2, 1],
            [2, 2, 2, 2],
            [3, 3, 3, 3],
            [1, 1, 1, 1],
            [2, 2, 2, 2]
        ]
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            large_services,
        )
        
        # Перевіряємо, що всі мікросервіси розподілені
        all_services = set()
        for service_group in group_services:
            all_services.update(service_group)
        self.assertEqual(all_services, set(range(len(large_services))))

        # Тест 4: Дві групи по 3 (жодна пара не стабільна, але трійки стабільні)
        microservices_6 = [
            [10, 0, 1],  # 0
            [1, 10, 0],  # 1
            [0, 1, 10],  # 2
            [10, 0, 2],  # 3
            [2, 10, 0],  # 4
            [0, 2, 10],  # 5
        ]
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices_6,
        )
        # Має бути дві групи по 3
        group_sizes = sorted([len(g) for g in group_services])
        self.assertEqual(group_sizes, [3, 3], "Має бути дві групи по 3")
        # Жодна пара не є стабільною
        for group in group_services:
            for i, j in itertools.combinations(range(len(group)), 2):
                pair = [microservices_6[group[i]], microservices_6[group[j]]]
                cv = calculate_stability(pair)
                self.assertGreaterEqual(cv, 20.0, "Жодна пара не має бути стабільною")
            # Але трійка має бути стабільною
            triple = [microservices_6[idx] for idx in group]
            cv = calculate_stability(triple)
            self.assertLess(cv, 20.0, "Трійка має бути стабільною")

        # Тест 5: Дві групи по 4 (жодна пара чи трійка не стабільна, але четвірки стабільні)
        microservices_8 = [
            [12, 0, 0, 0],  # 0
            [0, 12, 0, 0],  # 1
            [0, 0, 12, 0],  # 2
            [0, 0, 0, 12],  # 3
            [12, 0, 0, 0],  # 4
            [0, 12, 0, 0],  # 5
            [0, 0, 12, 0],  # 6
            [0, 0, 0, 12],  # 7
        ]
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices_8,
        )
        # Має бути дві групи по 4
        group_sizes = sorted([len(g) for g in group_services])
        self.assertEqual(group_sizes, [4, 4], "Має бути дві групи по 4")
        # Жодна пара чи трійка не є стабільною
        for group in group_services:
            for i, j in itertools.combinations(range(len(group)), 2):
                pair = [microservices_8[group[i]], microservices_8[group[j]]]
                cv = calculate_stability(pair)
                self.assertGreaterEqual(cv, 20.0, "Жодна пара не має бути стабільною")
            for i, j, k in itertools.combinations(range(len(group)), 3):
                triple = [microservices_8[group[i]], microservices_8[group[j]], microservices_8[group[k]]]
                cv = calculate_stability(triple)
                self.assertGreaterEqual(cv, 20.0, "Жодна трійка не має бути стабільною")
            # Але четвірка має бути стабільною
            quad = [microservices_8[idx] for idx in group]
            cv = calculate_stability(quad)
            self.assertLess(cv, 20.0, "Четвірка має бути стабільною")

    def test_stability_threshold(self):
        # Тест на перевищення порогу стабільності
        microservices = [
            [1, 2, 3, 4],    # Стабільний
            [4, 3, 2, 1],    # Стабільний
            [1, 10, 1, 10],  # Нестабільний
            [10, 1, 10, 1]   # Нестабільний
        ]
        
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices,
            max_group_size=2,
            stability_threshold=20.0
        )
        
        # Перевіряємо, що нестабільні мікросервіси не згруповані разом
        # (вони можуть бути в окремих групах або розділені на базові/пікові компоненти)
        for group in group_services:
            if len(group) > 1:
                # Якщо це група з більше ніж одним елементом, перевіряємо її стабільність
                group_loads = [microservices[idx] for idx in group if idx < 1000 and idx >= 0]
                if len(group_loads) > 1:
                    cv = calculate_stability(group_loads)
                    self.assertLess(cv, 20.0, f"Група {group} має CV {cv}, що більше порогу 20.0")
        

        
        # Перевіряємо, що всі мікросервіси розподілені
        all_services = set()
        for service_group in group_services:
            original_indices = []
            for idx in service_group:
                if idx < 0:  # Піковий компонент
                    original_indices.append(-idx)
                elif idx >= 1000:  # Базовий компонент
                    original_indices.append(idx - 1000)
                else:  # Оригінальний індекс
                    original_indices.append(idx)
            all_services.update(original_indices)
        self.assertEqual(all_services, set(range(len(microservices))))

    def test_group_formation_criteria(self):
        # Тест на різні сценарії формування груп
        microservices = [
            # Група 1: Комплементарні патерни (мають утворити групу)
            [1, 10, 1, 10],   # 0: Піки на 2 і 4
            [10, 1, 10, 1],   # 1: Піки на 1 і 3
            
            # Група 2: Синхронні піки (не мають утворити групу)
            [1, 10, 1, 10],   # 2: Піки на 2 і 4
            [1, 10, 1, 10],   # 3: Такі ж піки
            
            # Група 3: Різні патерни (мають утворити групу)
            [2, 2, 2, 2],     # 4: Стабільний
            [3, 3, 3, 3],     # 5: Стабільний
            
            # Група 4: Комплементарні піки (мають утворити стабільну групу)
            [1, 20, 1, 20],   # 6: Великі піки
            [20, 1, 20, 1]    # 7: Великі піки в інший час
        ]
        
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices,
            max_group_size=2,
            stability_threshold=20.0
        )
        
        # Перевіряємо, що комплементарні патерни (0,1) утворили групу
        complementary_grouped = False
        for group in group_services:
            if 0 in group and 1 in group:
                complementary_grouped = True
                # Перевіряємо стабільність групи
                group_loads = [microservices[idx] for idx in group if idx < 1000 and idx >= 0]
                cv = calculate_stability(group_loads)
                self.assertLess(cv, 20.0, "Комплементарна група має бути стабільною")
        self.assertTrue(complementary_grouped, "Комплементарні патерни мають бути згруповані")
        
        # Перевіряємо, що синхронні піки (2,3) не утворили групу
        synchronous_grouped = False
        for group in group_services:
            if len(group) > 1 and 2 in group and 3 in group:
                synchronous_grouped = True
                # Якщо вони все ж згруповані, перевіряємо що це базові компоненти
                self.assertTrue(all(idx >= 1000 for idx in group), 
                              "Синхронні піки мають бути розділені на базові компоненти")
        self.assertFalse(synchronous_grouped, "Синхронні піки не мають бути в одній групі")
        
        # Перевіряємо, що базові компоненти (2,3) утворили групу
        base_components_grouped = False
        for group in group_services:
            if len(group) > 1 and all(idx >= 1000 for idx in group):
                # Перевіряємо, чи це базові компоненти мікросервісів 2 і 3
                original_indices = [idx - 1000 for idx in group]
                if 2 in original_indices and 3 in original_indices:
                    base_components_grouped = True
                    # Перевіряємо стабільність групи базових компонентів
                    # Використовуємо базові компоненти з groups, а не оригінальні навантаження
                    group_loads = [groups[i][0] for i in range(len(groups)) if group_services[i] == group]
                    cv = calculate_stability(group_loads)
                    self.assertLess(cv, 20.0, "Група базових компонентів має бути стабільною")
        self.assertTrue(base_components_grouped, "Базові компоненти мають утворити стабільну групу")
        
        # Перевіряємо, що стабільні патерни (4,5) утворили групу
        stable_grouped = False
        for group in group_services:
            if 4 in group and 5 in group:
                stable_grouped = True
                # Перевіряємо стабільність групи
                group_loads = [microservices[idx] for idx in group if idx < 1000 and idx >= 0]
                cv = calculate_stability(group_loads)
                self.assertLess(cv, 20.0, "Стабільна група має бути стабільною")
        self.assertTrue(stable_grouped, "Стабільні патерни мають бути згруповані")
        
        # Перевіряємо, що комплементарні піки (6,7) утворили стабільну групу
        complementary_peaks_grouped = False
        for group in group_services:
            if 6 in group and 7 in group:
                complementary_peaks_grouped = True
                # Перевіряємо стабільність групи
                group_loads = [microservices[idx] for idx in group if idx < 1000 and idx >= 0]
                cv = calculate_stability(group_loads)
                self.assertLess(cv, 20.0, "Група з комплементарними піками має бути стабільною")
        self.assertTrue(complementary_peaks_grouped, "Комплементарні піки мають бути згруповані")

if __name__ == '__main__':
    unittest.main() 