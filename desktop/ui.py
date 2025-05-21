import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
from typing import List, Dict, Any, Tuple

from shared.db_input import DBInput
from shared.db_output import DBOutput
from shared.group_finder import form_multiple_knapsack_groups, split_microservice_load
from shared.visualization import Visualizer

class MicroserviceGroupingApp:
    """
    Головний клас додатку для групування мікросервісів
    """
    def __init__(self, root):
        """
        Ініціалізація додатку
        
        Args:
            root: Кореневий віджет Tkinter
        """
        self.root = root
        self.root.title("Групування мікросервісів")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Ініціалізація змінних
        self.metric_types = ["CPU", "RAM", "CHANNEL"]
        self.available_dates = []
        self.available_times = []
        self.microservices = []
        self.service_names = []
        self.groups = []
        self.group_services = []
        self.slot_sums = []
        
        # Ініціалізація об'єктів
        self.db_input = DBInput()
        self.db_output = DBOutput()
        self.visualizer = Visualizer()
        
        # Створення інтерфейсу
        self._create_widgets()
        
        # Завантаження доступних дат
        self._load_available_dates()
    
    def _create_widgets(self):
        """
        Створення віджетів інтерфейсу
        """
        # Створення головного фрейму
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для параметрів
        params_frame = ttk.LabelFrame(main_frame, text="Параметри групування", padding="10")
        params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Тип метрики
        ttk.Label(params_frame, text="Тип метрики:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.metric_var = tk.StringVar(value=self.metric_types[0])
        metric_combo = ttk.Combobox(params_frame, textvariable=self.metric_var, values=self.metric_types, state="readonly")
        metric_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        metric_combo.bind("<<ComboboxSelected>>", self._on_metric_selected)
        
        # Дата
        ttk.Label(params_frame, text="Дата:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(params_frame, textvariable=self.date_var, state="readonly")
        self.date_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.date_combo.bind("<<ComboboxSelected>>", self._on_date_selected)
        
        # Час
        ttk.Label(params_frame, text="Час:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        self.time_var = tk.StringVar()
        self.time_combo = ttk.Combobox(params_frame, textvariable=self.time_var, state="readonly")
        self.time_combo.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)
        
        # Максимальний розмір групи
        ttk.Label(params_frame, text="Макс. розмір групи:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.group_size_var = tk.IntVar(value=4)
        group_size_spin = ttk.Spinbox(params_frame, from_=2, to=10, textvariable=self.group_size_var, width=5)
        group_size_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Коефіцієнт варіації
        ttk.Label(params_frame, text="Коефіцієнт варіації (%):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.stability_threshold_var = tk.DoubleVar(value=20.0)
        stability_threshold_spin = ttk.Spinbox(params_frame, from_=5.0, to=50.0, increment=0.5, 
                                             textvariable=self.stability_threshold_var, width=5)
        stability_threshold_spin.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Кнопка запуску групування
        self.run_button = ttk.Button(params_frame, text="Запустити групування", command=self._run_grouping)
        self.run_button.grid(row=1, column=4, sticky=tk.E, padx=5, pady=5)
        
        # Кнопка перегляду існуючих варіантів групування
        self.view_saved_button = ttk.Button(params_frame, text="Переглянути збережені групування", 
                                           command=self._open_saved_groupings)
        self.view_saved_button.grid(row=1, column=5, sticky=tk.E, padx=5, pady=5)
        
        # Кнопка довідки
        help_frame = ttk.Frame(main_frame)
        help_frame.pack(fill=tk.X, padx=5, pady=2)
        self.help_button = ttk.Button(help_frame, text="Довідка", command=self._show_help)
        self.help_button.pack(side=tk.RIGHT, padx=5)
        
        # Фрейм для результатів
        self.results_frame = ttk.LabelFrame(main_frame, text="Результати групування", padding="10")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Notebook для різних візуалізацій
        self.notebook = ttk.Notebook(self.results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладки для різних візуалізацій
        self.tab_microservices = ttk.Frame(self.notebook)
        self.tab_group_load = ttk.Frame(self.notebook)
        self.tab_stability = ttk.Frame(self.notebook)
        self.tab_statistics = ttk.Frame(self.notebook)
        self.tab_base_peak = ttk.Frame(self.notebook)
        self.tab_load_distribution = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_microservices, text="Мікросервіси")
        self.notebook.add(self.tab_group_load, text="Навантаження груп")
        self.notebook.add(self.tab_stability, text="Стабільність")
        self.notebook.add(self.tab_statistics, text="Статистика")
        self.notebook.add(self.tab_base_peak, text="Базові/пікові компоненти")
        self.notebook.add(self.tab_load_distribution, text="Розподіл навантаження")
        
        # Фрейм для статусу
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Статус
        self.status_var = tk.StringVar(value="Готовий до роботи")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
    
    def _load_available_dates(self):
        """
        Завантаження доступних дат з бази даних
        """
        try:
            self.status_var.set("Завантаження доступних дат...")
            
            # Отримання списку доступних дат
            query = "SELECT DISTINCT date FROM processed_metrics ORDER BY date"
            self.db_input.cursor.execute(query)
            results = self.db_input.cursor.fetchall()
            
            self.available_dates = [row["date"].strftime("%Y-%m-%d") for row in results]
            self.date_combo["values"] = self.available_dates
            
            if self.available_dates:
                self.date_var.set(self.available_dates[0])
                self._on_date_selected()
            
            self.status_var.set(f"Знайдено {len(self.available_dates)} доступних дат")
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при завантаженні доступних дат: {e}")
            self.status_var.set("Помилка при завантаженні доступних дат")
    
    def _on_metric_selected(self, event=None):
        """
        Обробник події вибору типу метрики
        """
        # При зміні типу метрики, оновлюємо доступні дати
        self._load_available_dates()
    
    def _on_date_selected(self, event=None):
        """
        Обробник події вибору дати
        """
        try:
            self.status_var.set("Завантаження доступних часів...")
            
            # Отримання списку доступних часів для вибраної дати
            query = "SELECT DISTINCT time FROM processed_metrics WHERE date = %s ORDER BY time"
            self.db_input.cursor.execute(query, (self.date_var.get(),))
            results = self.db_input.cursor.fetchall()
            
            # Конвертація timedelta в рядок формату HH:MM:SS
            self.available_times = []
            for row in results:
                # Перевірка типу
                if isinstance(row["time"], datetime.timedelta):
                    # Конвертація timedelta в секунди
                    total_seconds = int(row["time"].total_seconds())
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    self.available_times.append(time_str)
                else:
                    # Якщо це не timedelta, спробуємо використати strftime
                    self.available_times.append(row["time"].strftime("%H:%M:%S"))
            
            self.time_combo["values"] = self.available_times
            
            if self.available_times:
                self.time_var.set(self.available_times[0])
            
            self.status_var.set(f"Знайдено {len(self.available_times)} доступних часів")
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при завантаженні доступних часів: {e}")
            self.status_var.set("Помилка при завантаженні доступних часів")
    
    def _run_grouping(self):
        """
        Запуск процесу групування мікросервісів
        """
        try:
            # Перевірка вибору параметрів
            if not self.date_var.get() or not self.time_var.get():
                messagebox.showwarning("Попередження", "Виберіть дату та час")
                return
            
            self.status_var.set("Отримання даних з бази даних...")
            
            # Отримання даних з бази даних
            metric_type = self.metric_var.get()
            date = self.date_var.get()
            time = self.time_var.get()
            
            self.microservices, self.service_names = self.db_input.get_data_for_algorithm(
                metric_type, date, time
            )
            
            if not self.microservices:
                messagebox.showwarning("Попередження", "Немає даних для вибраних параметрів")
                self.status_var.set("Немає даних для вибраних параметрів")
                return
            
            self.status_var.set(f"Отримано дані для {len(self.microservices)} мікросервісів")
            
            # Формування груп
            max_group_size = self.group_size_var.get()
            stability_threshold = self.stability_threshold_var.get()
            
            self.status_var.set("Формування груп...")
            self.groups, self.group_services, self.slot_sums = form_multiple_knapsack_groups(
                self.microservices, max_group_size=max_group_size, stability_threshold=stability_threshold
            )
            
            self.status_var.set(f"Сформовано {len(self.groups)} груп")
            
            # Збереження результатів в базу даних
            self.status_var.set("Збереження результатів у базу даних...")
            records_count = self.db_output.save_grouping_results(
                self.groups, 
                self.group_services, 
                self.service_names, 
                metric_type, 
                date, 
                time
            )
            
            if records_count > 0:
                self.status_var.set(f"Сформовано {len(self.groups)} груп. Збережено {records_count} записів у базу даних.")
            else:
                self.status_var.set(f"Сформовано {len(self.groups)} груп. Помилка при збереженні в базу даних.")
            
            # Відображення результатів
            self._show_results()
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при групуванні мікросервісів: {e}")
            self.status_var.set("Помилка при групуванні мікросервісів")
    
    def _show_results(self):
        """
        Відображення результатів групування
        """
        # Очищення вкладок
        for widget in self.tab_microservices.winfo_children():
            widget.destroy()
        for widget in self.tab_group_load.winfo_children():
            widget.destroy()
        for widget in self.tab_stability.winfo_children():
            widget.destroy()
        for widget in self.tab_statistics.winfo_children():
            widget.destroy()
        for widget in self.tab_base_peak.winfo_children():
            widget.destroy()
        for widget in self.tab_load_distribution.winfo_children():
            widget.destroy()
        
        # Вкладка "Мікросервіси"
        self._create_microservices_tab()
        
        # Вкладка "Навантаження груп"
        self._create_group_load_tab()
        
        # Вкладка "Стабільність"
        self._create_stability_tab()
        
        # Вкладка "Статистика"
        self._create_statistics_tab()
        
        # Вкладка "Базові/пікові компоненти"
        self._create_base_peak_tab()
        
        # Вкладка "Розподіл навантаження"
        self._create_load_distribution_tab()
        
        # Перехід на першу вкладку
        self.notebook.select(0)
    
    def _create_microservices_tab(self):
        """
        Створення вкладки "Мікросервіси"
        """
        # Створення фігури matplotlib
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Побудова графіка
        for i, (service, name) in enumerate(zip(self.microservices, self.service_names)):
            ax.plot(service, label=name, marker='o', linestyle='-', markersize=4)
        
        ax.set_title("Часові ряди мікросервісів")
        ax.set_xlabel("Часовий слот")
        ax.set_ylabel("Навантаження")
        ax.legend(loc='best')
        ax.grid(True)
        
        # Додавання фігури на вкладку
        canvas = FigureCanvasTkAgg(fig, master=self.tab_microservices)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_group_load_tab(self):
        """
        Створення вкладки "Навантаження груп"
        """
        # Створення фігури matplotlib
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Побудова графіка
        for i, group in enumerate(self.groups):
            # Обчислення загального навантаження групи
            time_slots = len(group[0]) if group else 0
            total_load = [0] * time_slots
            
            for service in group:
                for t in range(time_slots):
                    total_load[t] += service[t]
            
            # Побудова графіка для групи
            ax.plot(total_load, label=f"Група {i+1}", marker='o', linestyle='-', markersize=4)
        
        ax.set_title("Загальне навантаження груп")
        ax.set_xlabel("Часовий слот")
        ax.set_ylabel("Загальне навантаження")
        ax.legend(loc='best')
        ax.grid(True)
        
        # Додавання фігури на вкладку
        canvas = FigureCanvasTkAgg(fig, master=self.tab_group_load)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_stability_tab(self):
        """
        Створення вкладки "Стабільність"
        """
        # Створення фігури matplotlib
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Обчислення коефіцієнтів варіації
        cv_values = []
        group_labels = []
        
        for i, group in enumerate(self.groups):
            # Обчислення загального навантаження групи
            time_slots = len(group[0]) if group else 0
            total_load = [0] * time_slots
            
            for service in group:
                for t in range(time_slots):
                    total_load[t] += service[t]
            
            # Обчислення коефіцієнта варіації
            mean = sum(total_load) / len(total_load) if total_load else 0
            variance = sum((x - mean) ** 2 for x in total_load) / len(total_load) if total_load else 0
            std_dev = variance ** 0.5
            cv = (std_dev / mean) * 100 if mean > 0 else float('inf')
            
            cv_values.append(cv if cv != float('inf') else 100)  # Обмеження для візуалізації
            group_labels.append(f"Група {i+1}")
        
        # Побудова графіка
        ax.bar(group_labels, cv_values)
        ax.set_title("Порівняння стабільності груп за коефіцієнтом варіації")
        ax.set_xlabel("Група")
        ax.set_ylabel("Коефіцієнт варіації (%)")
        ax.grid(True, axis='y')
        
        # Додавання фігури на вкладку
        canvas = FigureCanvasTkAgg(fig, master=self.tab_stability)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_statistics_tab(self):
        """
        Створення вкладки "Статистика"
        """
        # Створення фрейму для статистики
        stats_frame = ttk.Frame(self.tab_statistics, padding="10")
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # Створення текстового поля для статистики
        stats_text = tk.Text(stats_frame, wrap=tk.WORD, width=80, height=20)
        stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Додавання скролбару
        scrollbar = ttk.Scrollbar(stats_text, command=stats_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        stats_text.config(yscrollcommand=scrollbar.set)
        
        # Підготовка даних для статистики
        group_sizes = [len(group) for group in self.group_services]
        
        # Обчислення середнього навантаження для кожної групи
        mean_loads = []
        peak_loads = []
        stability_values = []
        
        for group in self.groups:
            # Обчислення загального навантаження групи
            time_slots = len(group[0]) if group else 0
            total_load = [0] * time_slots
            
            for service in group:
                for t in range(time_slots):
                    total_load[t] += service[t]
            
            mean_loads.append(sum(total_load) / len(total_load) if total_load else 0)
            peak_loads.append(max(total_load) if total_load else 0)
            
            # Обчислення коефіцієнту стабільності (CV)
            from shared.group_finder import calculate_stability
            stability = calculate_stability(group)
            stability_values.append(stability)
        
        # Додавання статистики в текстове поле
        stats_text.insert(tk.END, f"Загальна статистика:\n")
        stats_text.insert(tk.END, f"- Кількість груп: {len(self.groups)}\n")
        stats_text.insert(tk.END, f"- Кількість мікросервісів: {len(self.microservices)}\n")
        stats_text.insert(tk.END, f"- Тип метрики: {self.metric_var.get()}\n")
        stats_text.insert(tk.END, f"- Дата: {self.date_var.get()}\n")
        stats_text.insert(tk.END, f"- Час: {self.time_var.get()}\n")
        stats_text.insert(tk.END, f"- Максимальний розмір групи: {self.group_size_var.get()}\n")
        stats_text.insert(tk.END, f"- Коефіцієнт варіації: {self.stability_threshold_var.get()}%\n\n")
        
        stats_text.insert(tk.END, "Статистика по групах:\n")
        stats_text.insert(tk.END, "-" * 50 + "\n")
        
        for i, (size, mean, peak, stability) in enumerate(zip(group_sizes, mean_loads, peak_loads, stability_values)):
            stats_text.insert(tk.END, f"Група {i+1}:\n")
            stats_text.insert(tk.END, f"  Кількість мікросервісів: {size}\n")
            stats_text.insert(tk.END, f"  Середнє навантаження: {mean:.2f}\n")
            stats_text.insert(tk.END, f"  Пікове навантаження: {peak:.2f}\n")
            stats_text.insert(tk.END, f"  Коефіцієнт стабільності: {stability:.2f}%\n")
            
            # Отримання списку мікросервісів у групі з урахуванням базових та пікових компонентів
            services_in_group = []
            for idx in self.group_services[i]:
                if idx >= 1000:  # Базовий компонент
                    real_idx = idx - 1000
                    if 0 <= real_idx < len(self.service_names):
                        services_in_group.append(f"{self.service_names[real_idx]} (базовий)")
                elif idx < 0:  # Піковий компонент
                    real_idx = -idx
                    if 0 <= real_idx < len(self.service_names):
                        services_in_group.append(f"{self.service_names[real_idx]} (піковий)")
                else:  # Звичайний мікросервіс
                    if 0 <= idx < len(self.service_names):
                        services_in_group.append(self.service_names[idx])
            
            stats_text.insert(tk.END, f"  Мікросервіси: {services_in_group}\n")
            
            # Додавання часових рядів мікросервісів у групі
            stats_text.insert(tk.END, "  Часові ряди мікросервісів у групі:\n")
            
            for j, service_idx in enumerate(self.group_services[i]):
                service_name = ""
                service_data = []
                
                if service_idx >= 1000:  # Базовий компонент
                    real_idx = service_idx - 1000
                    if 0 <= real_idx < len(self.service_names):
                        service_name = f"{self.service_names[real_idx]} (базовий)"
                        service_data = self.groups[i][j]
                elif service_idx < 0:  # Піковий компонент
                    real_idx = -service_idx
                    if 0 <= real_idx < len(self.service_names):
                        service_name = f"{self.service_names[real_idx]} (піковий)"
                        service_data = self.groups[i][j]
                else:  # Звичайний мікросервіс
                    if 0 <= service_idx < len(self.service_names):
                        service_name = self.service_names[service_idx]
                        service_data = self.groups[i][j]
                
                # Форматування часового ряду для виводу
                time_series_str = " ".join([f"{val:.2f}" for val in service_data])
                stats_text.insert(tk.END, f"    {service_name}: [{time_series_str}]\n")
            
            # Додавання загального навантаження групи
            time_slots = len(self.groups[i][0]) if self.groups[i] else 0
            total_load = [0] * time_slots
            
            for service in self.groups[i]:
                for t in range(time_slots):
                    total_load[t] += service[t]
            
            total_load_str = " ".join([f"{val:.2f}" for val in total_load])
            stats_text.insert(tk.END, f"  Загальне навантаження групи: [{total_load_str}]\n")
            stats_text.insert(tk.END, "-" * 50 + "\n")
        
        # Заборона редагування тексту
        stats_text.config(state=tk.DISABLED)
    
    def _create_base_peak_tab(self):
        """
        Створення вкладки "Базові/пікові компоненти"
        """
        # Знаходимо мікросервіси, які були розділені на базові та пікові компоненти
        split_indices = set()
        
        for group in self.group_services:
            for idx in group:
                if idx >= 1000 or idx < 0:  # Базовий або піковий компонент
                    # Визначаємо реальний індекс
                    real_idx = idx - 1000 if idx >= 1000 else -idx
                    split_indices.add(real_idx)
        
        if not split_indices:
            # Якщо немає розділених мікросервісів
            ttk.Label(self.tab_base_peak, text="Немає мікросервісів, які були розділені на базові та пікові компоненти").pack(pady=20)
            return
        
        # Створення фрейму для вибору мікросервісу
        select_frame = ttk.Frame(self.tab_base_peak, padding="10")
        select_frame.pack(fill=tk.X)
        
        ttk.Label(select_frame, text="Виберіть мікросервіс:").pack(side=tk.LEFT, padx=5)
        
        # Створення списку розділених мікросервісів
        split_names = [self.service_names[idx] for idx in split_indices]
        
        # Змінна для вибору мікросервісу
        self.selected_split_var = tk.StringVar(value=split_names[0] if split_names else "")
        
        # Комбобокс для вибору мікросервісу
        split_combo = ttk.Combobox(select_frame, textvariable=self.selected_split_var, values=split_names, state="readonly")
        split_combo.pack(side=tk.LEFT, padx=5)
        split_combo.bind("<<ComboboxSelected>>", self._on_split_selected)
        
        # Фрейм для графіка
        self.split_graph_frame = ttk.Frame(self.tab_base_peak, padding="10")
        self.split_graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Відображення першого розділеного мікросервісу
        if split_names:
            self._on_split_selected()
    
    def _on_split_selected(self, event=None):
        """
        Обробник події вибору розділеного мікросервісу
        """
        # Очищення фрейму для графіка
        for widget in self.split_graph_frame.winfo_children():
            widget.destroy()
        
        # Отримання індексу вибраного мікросервісу
        selected_name = self.selected_split_var.get()
        selected_idx = self.service_names.index(selected_name)
        
        # Розділення мікросервісу на базовий та піковий компоненти
        base, peak = split_microservice_load(self.microservices[selected_idx])
        
        # Створення фігури matplotlib
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Побудова графіків
        ax.plot(base, label="Базовий компонент", marker='o', linestyle='-', color='blue', markersize=4)
        ax.plot(peak, label="Піковий компонент", marker='x', linestyle='--', color='red', markersize=4)
        ax.plot([b + p for b, p in zip(base, peak)], label="Загальне навантаження", 
                marker='s', linestyle='-.', color='green', markersize=4)
        
        ax.set_title(f"Розділення навантаження для мікросервісу: {selected_name}")
        ax.set_xlabel("Часовий слот")
        ax.set_ylabel("Навантаження")
        ax.legend(loc='best')
        ax.grid(True)
        
        # Додавання фігури на вкладку
        canvas = FigureCanvasTkAgg(fig, master=self.split_graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_load_distribution_tab(self):
        """
        Створення вкладки "Розподіл навантаження"
        """
        if not self.groups:
            ttk.Label(self.tab_load_distribution, text="Немає даних для відображення").pack(pady=20)
            return
        
        # Створення фрейму для вибору групи
        select_frame = ttk.Frame(self.tab_load_distribution, padding="10")
        select_frame.pack(fill=tk.X)
        
        ttk.Label(select_frame, text="Виберіть групу:").pack(side=tk.LEFT, padx=5)
        
        # Створення списку груп
        group_names = [f"Група {i+1}" for i in range(len(self.groups))]
        
        # Змінна для вибору групи
        self.selected_group_var = tk.StringVar(value=group_names[0] if group_names else "")
        
        # Комбобокс для вибору групи
        group_combo = ttk.Combobox(select_frame, textvariable=self.selected_group_var, values=group_names, state="readonly")
        group_combo.pack(side=tk.LEFT, padx=5)
        group_combo.bind("<<ComboboxSelected>>", self._on_group_selected)
        
        # Фрейм для графіка
        self.load_distribution_frame = ttk.Frame(self.tab_load_distribution, padding="10")
        self.load_distribution_frame.pack(fill=tk.BOTH, expand=True)
        
        # Відображення першої групи
        if group_names:
            self._on_group_selected()
    
    def _on_group_selected(self, event=None):
        """
        Обробник події вибору групи для відображення розподілу навантаження
        """
        # Очищення фрейму для графіка
        for widget in self.load_distribution_frame.winfo_children():
            widget.destroy()
        
        # Отримання індексу вибраної групи
        selected_group = self.selected_group_var.get()
        group_idx = int(selected_group.split(" ")[1]) - 1
        
        # Отримання даних для вибраної групи
        group = self.groups[group_idx]
        group_services = self.group_services[group_idx]
        
        # Кількість часових слотів
        time_slots = len(group[0]) if group else 0
        
        # Створення фігури matplotlib
        fig = plt.figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        # Знаходження максимального навантаження для групи
        max_load = 0
        for t in range(time_slots):
            slot_load = sum(service[t] for service in group)
            max_load = max(max_load, slot_load)
        
        # Підготовка даних для стекової гістограми
        bottoms = [0] * time_slots
        
        # Кольори для мікросервісів
        colors = plt.cm.tab20(range(len(group)))
        
        # Підготовка даних для легенди
        legend_patches = []
        
        # Для кожного мікросервісу в групі
        for i, (service, service_idx) in enumerate(zip(group, group_services)):
            # Визначаємо назву мікросервісу
            if service_idx >= 1000:  # Базовий компонент
                real_idx = service_idx - 1000
                if 0 <= real_idx < len(self.service_names):
                    service_name = f"{self.service_names[real_idx]} (базовий)"
            elif service_idx < 0:  # Піковий компонент
                real_idx = -service_idx
                if 0 <= real_idx < len(self.service_names):
                    service_name = f"{self.service_names[real_idx]} (піковий)"
            else:  # Звичайний мікросервіс
                if 0 <= service_idx < len(self.service_names):
                    service_name = self.service_names[service_idx]
                else:
                    service_name = f"Сервіс {i+1}"
            
            # Додаємо стовпчик для цього мікросервісу
            bars = ax.bar(range(time_slots), service, bottom=bottoms, label=service_name, 
                         color=colors[i % len(colors)], edgecolor='black', linewidth=0.5)
            
            # Додаємо патч для легенди
            legend_patches.append(plt.Rectangle((0, 0), 1, 1, color=colors[i % len(colors)], label=service_name))
            
            # Оновлюємо нижні межі для наступного мікросервісу
            bottoms = [bottoms[t] + service[t] for t in range(time_slots)]
        
        # Додаємо "вільне місце" як прозору частину стовпчиків
        free_space = [max_load - b for b in bottoms]
        ax.bar(range(time_slots), free_space, bottom=bottoms, alpha=0.2, hatch='///', 
              label="Вільне місце", edgecolor='gray', linewidth=0.5)
        legend_patches.append(plt.Rectangle((0, 0), 1, 1, alpha=0.2, hatch='///', label="Вільне місце"))
        
        # Налаштування графіка
        ax.set_title(f"Розподіл навантаження для {selected_group}")
        ax.set_xlabel("Часовий слот")
        ax.set_ylabel("Навантаження")
        ax.set_xticks(range(time_slots))
        ax.set_xticklabels([f"{t+1}" for t in range(time_slots)])
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Встановлюємо межі осі Y
        ax.set_ylim(0, max_load)
        
        # Додаємо легенду
        ax.legend(handles=legend_patches, loc='upper right', title="Мікросервіси")
        
        # Додавання фігури на вкладку
        canvas = FigureCanvasTkAgg(fig, master=self.load_distribution_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Додаємо інформацію про стабільність групи
        from shared.group_finder import calculate_stability
        stability = calculate_stability(group)
        
        info_frame = ttk.Frame(self.load_distribution_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text=f"Коефіцієнт стабільності групи: {stability:.2f}%", 
                 font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=10)
    
    def _open_saved_groupings(self):
        """
        Відкриває вікно для перегляду збережених варіантів групування
        """
        saved_groupings_window = SavedGroupingsWindow(self.root, self.db_output, self)
        saved_groupings_window.grab_set()  # Робимо вікно модальним
    
    def _show_help(self):
        """
        Відображає вікно довідки з інформацією про параметри та графіки
        """
        help_window = HelpWindow(self.root)
        help_window.grab_set()  # Робимо вікно модальним
    
    def run(self):
        """
        Запуск додатку
        """
        self.root.mainloop()
    
    def __del__(self):
        """
        Деструктор для закриття з'єднання з базою даних
        """
        try:
            if hasattr(self, 'db_input'):
                self.db_input.close()
            if hasattr(self, 'db_output'):
                self.db_output.close()
        except:
            pass

class SavedGroupingsWindow(tk.Toplevel):
    """
    Вікно для перегляду збережених варіантів групування
    """
    def __init__(self, parent, db_output, main_app=None):
        super().__init__(parent)
        self.title("Збережені варіанти групування")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        self.db_output = db_output
        self.main_app = main_app  # Посилання на головний додаток
        self.selected_grouping = None
        self.selected_group_id = None
        
        # Створення віджетів
        self._create_widgets()
        
        # Завантаження доступних варіантів групування
        self._load_available_groupings()
    
    def _create_widgets(self):
        """
        Створення віджетів інтерфейсу
        """
        # Головний фрейм
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для таблиці варіантів групування
        groupings_frame = ttk.LabelFrame(main_frame, text="Доступні варіанти групування", padding="10")
        groupings_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Створення таблиці варіантів групування
        columns = ("date", "time", "metric_type", "num_groups")
        self.groupings_table = ttk.Treeview(groupings_frame, columns=columns, show="headings")
        
        # Заголовки стовпців
        self.groupings_table.heading("date", text="Дата")
        self.groupings_table.heading("time", text="Час")
        self.groupings_table.heading("metric_type", text="Тип метрики")
        self.groupings_table.heading("num_groups", text="Кількість груп")
        
        # Ширина стовпців
        self.groupings_table.column("date", width=100)
        self.groupings_table.column("time", width=100)
        self.groupings_table.column("metric_type", width=100)
        self.groupings_table.column("num_groups", width=100)
        
        # Додавання скролбару
        scrollbar = ttk.Scrollbar(groupings_frame, orient=tk.VERTICAL, command=self.groupings_table.yview)
        self.groupings_table.configure(yscroll=scrollbar.set)
        
        # Розміщення таблиці та скролбару
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.groupings_table.pack(fill=tk.BOTH, expand=True)
        
        # Додавання обробника події вибору рядка
        self.groupings_table.bind("<<TreeviewSelect>>", self._on_grouping_selected)
        
        # Фрейм для вибору групи та відображення мікросервісів
        group_frame = ttk.LabelFrame(main_frame, text="Мікросервіси у групі", padding="10")
        group_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Фрейм для вибору групи
        select_group_frame = ttk.Frame(group_frame)
        select_group_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(select_group_frame, text="Виберіть групу:").pack(side=tk.LEFT, padx=5)
        
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(select_group_frame, textvariable=self.group_var, state="readonly")
        self.group_combo.pack(side=tk.LEFT, padx=5)
        self.group_combo.bind("<<ComboboxSelected>>", self._on_group_selected)
        
        # Створення таблиці мікросервісів
        services_frame = ttk.Frame(group_frame)
        services_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("service_name", "component_type")
        self.services_table = ttk.Treeview(services_frame, columns=columns, show="headings")
        
        # Заголовки стовпців
        self.services_table.heading("service_name", text="Назва мікросервісу")
        self.services_table.heading("component_type", text="Тип компоненту")
        
        # Ширина стовпців
        self.services_table.column("service_name", width=300)
        self.services_table.column("component_type", width=150)
        
        # Додавання скролбару
        scrollbar = ttk.Scrollbar(services_frame, orient=tk.VERTICAL, command=self.services_table.yview)
        self.services_table.configure(yscroll=scrollbar.set)
        
        # Розміщення таблиці та скролбару
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.services_table.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для кнопок
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Кнопка завантаження в головний інтерфейс
        self.load_button = ttk.Button(buttons_frame, text="Завантажити в головний інтерфейс", 
                                     command=self._load_to_main_interface)
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка закриття
        close_button = ttk.Button(buttons_frame, text="Закрити", command=self.destroy)
        close_button.pack(side=tk.RIGHT, padx=5)
    
    def _load_available_groupings(self):
        """
        Завантаження доступних варіантів групування з бази даних
        """
        try:
            # Очищення таблиці
            for item in self.groupings_table.get_children():
                self.groupings_table.delete(item)
            
            # Запит для отримання доступних варіантів групування
            query = """
            SELECT 
                date, 
                time, 
                metric_type, 
                COUNT(DISTINCT group_id) AS num_groups
            FROM grouping_results
            GROUP BY date, time, metric_type
            ORDER BY date DESC, time DESC
            """
            
            self.db_output.cursor.execute(query)
            results = self.db_output.cursor.fetchall()
            
            # Додавання результатів у таблицю
            for row in results:
                date_str = row["date"].strftime("%Y-%m-%d")
                time_str = str(row["time"])
                metric_type = row["metric_type"]
                num_groups = row["num_groups"]
                
                self.groupings_table.insert("", tk.END, values=(date_str, time_str, metric_type, num_groups))
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при завантаженні варіантів групування: {e}")
    
    def _on_grouping_selected(self, event):
        """
        Обробник події вибору варіанту групування
        """
        # Отримання вибраного елемента
        selected_item = self.groupings_table.selection()
        if not selected_item:
            return
        
        # Отримання даних вибраного елемента
        item_data = self.groupings_table.item(selected_item[0], "values")
        date_str = item_data[0]
        time_str = item_data[1]
        metric_type = item_data[2]
        
        # Збереження вибраного варіанту групування
        self.selected_grouping = (date_str, time_str, metric_type)
        
        # Завантаження доступних груп для вибраного варіанту групування
        self._load_available_groups()
    
    def _load_available_groups(self):
        """
        Завантаження доступних груп для вибраного варіанту групування
        """
        try:
            # Очищення комбобоксу
            self.group_combo["values"] = []
            self.group_var.set("")
            
            # Очищення таблиці мікросервісів
            for item in self.services_table.get_children():
                self.services_table.delete(item)
            
            if not self.selected_grouping:
                return
            
            date_str, time_str, metric_type = self.selected_grouping
            
            # Запит для отримання доступних груп
            query = """
            SELECT DISTINCT group_id
            FROM grouping_results
            WHERE date = %s AND time = %s AND metric_type = %s
            ORDER BY group_id
            """
            
            self.db_output.cursor.execute(query, (date_str, time_str, metric_type))
            results = self.db_output.cursor.fetchall()
            
            # Додавання результатів у комбобокс
            group_names = [f"Група {row['group_id']}" for row in results]
            self.group_combo["values"] = group_names
            
            if group_names:
                self.group_var.set(group_names[0])
                self._on_group_selected()
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при завантаженні груп: {e}")
    
    def _on_group_selected(self, event=None):
        """
        Обробник події вибору групи
        """
        # Очищення таблиці мікросервісів
        for item in self.services_table.get_children():
            self.services_table.delete(item)
        
        if not self.group_var.get():
            return
        
        # Отримання ID вибраної групи
        group_id = int(self.group_var.get().split(" ")[1])
        self.selected_group_id = group_id
        
        # Завантаження мікросервісів для вибраної групи
        self._load_group_services()
    
    def _load_group_services(self):
        """
        Завантаження мікросервісів для вибраної групи
        """
        try:
            if not self.selected_grouping or self.selected_group_id is None:
                return
            
            date_str, time_str, metric_type = self.selected_grouping
            
            # Запит для отримання мікросервісів у вибраній групі
            query = """
            SELECT service_name, component_type
            FROM grouping_results
            WHERE date = %s AND time = %s AND metric_type = %s AND group_id = %s
            ORDER BY service_name
            """
            
            self.db_output.cursor.execute(query, (date_str, time_str, metric_type, self.selected_group_id))
            results = self.db_output.cursor.fetchall()
            
            # Додавання результатів у таблицю
            for row in results:
                service_name = row["service_name"]
                component_type = row["component_type"]
                
                # Переклад типу компоненту
                if component_type == "original":
                    component_type_str = "Оригінальний"
                elif component_type == "base":
                    component_type_str = "Базовий"
                elif component_type == "peak":
                    component_type_str = "Піковий"
                else:
                    component_type_str = component_type
                
                self.services_table.insert("", tk.END, values=(service_name, component_type_str))
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при завантаженні мікросервісів: {e}")
    
    def _load_to_main_interface(self):
        """
        Завантажує вибраний варіант групування в головний інтерфейс
        """
        if not self.selected_grouping or self.main_app is None:
            messagebox.showwarning("Попередження", "Спочатку виберіть варіант групування")
            return
        
        try:
            date_str, time_str, metric_type = self.selected_grouping
            
            # Завантаження даних мікросервісів
            self.main_app.microservices, self.main_app.service_names = self.main_app.db_input.get_data_for_algorithm(
                metric_type, date_str, time_str
            )
            
            # Завантаження груп
            self.main_app.groups = []
            self.main_app.group_services = []
            
            # Отримання всіх груп для вибраного варіанту групування
            query = """
            SELECT DISTINCT group_id
            FROM grouping_results
            WHERE date = %s AND time = %s AND metric_type = %s
            ORDER BY group_id
            """
            
            self.db_output.cursor.execute(query, (date_str, time_str, metric_type))
            group_ids = [row["group_id"] for row in self.db_output.cursor.fetchall()]
            
            for group_id in group_ids:
                # Отримання мікросервісів для поточної групи
                query = """
                SELECT service_name, component_type
                FROM grouping_results
                WHERE date = %s AND time = %s AND metric_type = %s AND group_id = %s
                ORDER BY service_name
                """
                
                self.db_output.cursor.execute(query, (date_str, time_str, metric_type, group_id))
                services_in_group = self.db_output.cursor.fetchall()
                
                # Формування групи
                group = []
                group_indices = []
                
                for service_row in services_in_group:
                    service_name = service_row["service_name"]
                    component_type = service_row["component_type"]
                    
                    # Знаходження індексу мікросервісу
                    if service_name in self.main_app.service_names:
                        service_idx = self.main_app.service_names.index(service_name)
                        
                        # Визначення типу компоненту
                        if component_type == "original":
                            idx = service_idx
                        elif component_type == "base":
                            idx = service_idx + 1000  # Базовий компонент
                        elif component_type == "peak":
                            idx = -service_idx  # Піковий компонент
                        else:
                            continue
                        
                        # Додавання мікросервісу в групу
                        if 0 <= service_idx < len(self.main_app.microservices):
                            if component_type == "original":
                                group.append(self.main_app.microservices[service_idx])
                            elif component_type == "base":
                                # Розділення на базовий та піковий компоненти
                                base, _ = split_microservice_load(self.main_app.microservices[service_idx])
                                group.append(base)
                            elif component_type == "peak":
                                # Розділення на базовий та піковий компоненти
                                _, peak = split_microservice_load(self.main_app.microservices[service_idx])
                                group.append(peak)
                            
                            group_indices.append(idx)
                
                # Додавання групи в список груп
                if group:
                    self.main_app.groups.append(group)
                    self.main_app.group_services.append(group_indices)
            
            # Обчислення загального навантаження для кожної групи
            self.main_app.slot_sums = []
            for group in self.main_app.groups:
                time_slots = len(group[0]) if group else 0
                slot_sums = [0] * time_slots
                
                for service in group:
                    for t in range(time_slots):
                        slot_sums[t] += service[t]
                
                self.main_app.slot_sums.append(slot_sums)
            
            # Оновлення параметрів в інтерфейсі
            self.main_app.metric_var.set(metric_type)
            self.main_app.date_var.set(date_str)
            self.main_app.time_var.set(time_str)
            
            # Відображення результатів
            self.main_app._show_results()
            
            messagebox.showinfo("Інформація", f"Варіант групування успішно завантажено: {date_str}, {time_str}, {metric_type}")
            
            # Закриття вікна
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при завантаженні варіанту групування: {e}")

class HelpWindow(tk.Toplevel):
    """
    Вікно довідки з інформацією про параметри та графіки
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Довідка")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Створення віджетів
        self._create_widgets()
    
    def _create_widgets(self):
        """
        Створення віджетів інтерфейсу
        """
        # Головний фрейм
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook для різних розділів довідки
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладки для різних розділів довідки
        tab_parameters = ttk.Frame(notebook)
        tab_graphs = ttk.Frame(notebook)
        
        notebook.add(tab_parameters, text="Параметри")
        notebook.add(tab_graphs, text="Графіки та візуалізації")
        
        # Заповнення вкладки "Параметри"
        self._create_parameters_tab(tab_parameters)
        
        # Заповнення вкладки "Графіки та візуалізації"
        self._create_graphs_tab(tab_graphs)
        
        # Кнопка закриття
        close_button = ttk.Button(main_frame, text="Закрити", command=self.destroy)
        close_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def _create_parameters_tab(self, parent):
        """
        Заповнення вкладки "Параметри"
        """
        # Створення текстового поля з можливістю прокрутки
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        text = tk.Text(text_frame, wrap=tk.WORD, width=80, height=20)
        text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        
        # Додавання інформації про параметри
        text.insert(tk.END, "Параметри групування мікросервісів\n\n", "header")
        
        text.insert(tk.END, "Тип метрики:\n", "subheader")
        text.insert(tk.END, "Визначає тип метрики для аналізу навантаження мікросервісів. Доступні типи:\n")
        text.insert(tk.END, "• CPU - використання процесора\n")
        text.insert(tk.END, "• RAM - використання оперативної пам'яті\n")
        text.insert(tk.END, "• CHANNEL - використання мережевого каналу\n\n")
        
        text.insert(tk.END, "Дата та час:\n", "subheader")
        text.insert(tk.END, "Вибір дати та часу для аналізу даних з бази даних. Система відображає доступні дати та часи, для яких є дані в базі.\n\n")
        
        text.insert(tk.END, "Максимальний розмір групи:\n", "subheader")
        text.insert(tk.END, "Визначає максимальну кількість мікросервісів, які можуть бути включені в одну групу. Рекомендоване значення: 4.\n\n")
        
        text.insert(tk.END, "Коефіцієнт варіації (%):\n", "subheader")
        text.insert(tk.END, "Максимально допустимий коефіцієнт варіації для групи мікросервісів. Чим менше значення, тим стабільніша група.\n")
        text.insert(tk.END, "Коефіцієнт варіації обчислюється як відношення стандартного відхилення до середнього значення, помножене на 100%.\n")
        text.insert(tk.END, "Рекомендоване значення: 20%.\n\n")
        
        # Налаштування стилів тексту
        text.tag_configure("header", font=("TkDefaultFont", 14, "bold"))
        text.tag_configure("subheader", font=("TkDefaultFont", 12, "bold"))
        
        # Заборона редагування тексту
        text.config(state=tk.DISABLED)
    
    def _create_graphs_tab(self, parent):
        """
        Заповнення вкладки "Графіки та візуалізації"
        """
        # Створення текстового поля з можливістю прокрутки
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        text = tk.Text(text_frame, wrap=tk.WORD, width=80, height=20)
        text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        
        # Додавання інформації про графіки та візуалізації
        text.insert(tk.END, "Графіки та візуалізації\n\n", "header")
        
        text.insert(tk.END, "Вкладка 'Мікросервіси':\n", "subheader")
        text.insert(tk.END, "Відображає часові ряди навантаження для всіх мікросервісів. Кожна лінія представляє один мікросервіс.\n")
        text.insert(tk.END, "Цей графік дозволяє візуально оцінити характер навантаження кожного мікросервісу та виявити потенційні патерни.\n\n")
        
        text.insert(tk.END, "Вкладка 'Навантаження груп':\n", "subheader")
        text.insert(tk.END, "Відображає загальне навантаження для кожної сформованої групи мікросервісів.\n")
        text.insert(tk.END, "Цей графік дозволяє порівняти навантаження різних груп та оцінити їх стабільність.\n\n")
        
        text.insert(tk.END, "Вкладка 'Стабільність':\n", "subheader")
        text.insert(tk.END, "Відображає коефіцієнти варіації для кожної групи у вигляді стовпчикової діаграми.\n")
        text.insert(tk.END, "Чим нижчий стовпчик, тим стабільніша група. Групи з високим коефіцієнтом варіації мають нестабільне навантаження.\n\n")
        
        text.insert(tk.END, "Вкладка 'Статистика':\n", "subheader")
        text.insert(tk.END, "Відображає детальну статистику по кожній групі, включаючи:\n")
        text.insert(tk.END, "• Кількість мікросервісів у групі\n")
        text.insert(tk.END, "• Середнє навантаження групи\n")
        text.insert(tk.END, "• Пікове навантаження групи\n")
        text.insert(tk.END, "• Коефіцієнт стабільності групи\n")
        text.insert(tk.END, "• Список мікросервісів у групі\n")
        text.insert(tk.END, "• Часові ряди мікросервісів у групі\n")
        text.insert(tk.END, "• Загальне навантаження групи\n\n")
        
        text.insert(tk.END, "Вкладка 'Базові/пікові компоненти':\n", "subheader")
        text.insert(tk.END, "Відображає розділення мікросервісів на базові та пікові компоненти.\n")
        text.insert(tk.END, "Базовий компонент представляє стабільне навантаження мікросервісу, а піковий компонент - нестабільні піки навантаження.\n")
        text.insert(tk.END, "Цей графік дозволяє оцінити, наскільки успішно алгоритм розділив мікросервіси на компоненти.\n\n")
        
        text.insert(tk.END, "Вкладка 'Розподіл навантаження':\n", "subheader")
        text.insert(tk.END, "Відображає розподіл навантаження мікросервісів у вибраній групі за часовими слотами.\n")
        text.insert(tk.END, "Кожен стовпчик представляє один часовий слот, а різні кольори в стовпчику відповідають різним мікросервісам.\n")
        text.insert(tk.END, "Прозора частина стовпчика показує вільне місце (невикористане навантаження) в групі.\n")
        text.insert(tk.END, "Цей графік дозволяє детально проаналізувати розподіл навантаження в групі та виявити потенційні проблеми.\n\n")
        
        # Налаштування стилів тексту
        text.tag_configure("header", font=("TkDefaultFont", 14, "bold"))
        text.tag_configure("subheader", font=("TkDefaultFont", 12, "bold"))
        
        # Заборона редагування тексту
        text.config(state=tk.DISABLED)
    
    def _create_algorithm_tab(self, parent):
        """
        Заповнення вкладки "Алгоритм групування"
        """
        # Створення текстового поля з можливістю прокрутки
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        text = tk.Text(text_frame, wrap=tk.WORD, width=80, height=20)
        text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        
        # Додавання інформації про алгоритм групування
        text.insert(tk.END, "Алгоритм групування мікросервісів\n\n", "header")
        
        text.insert(tk.END, "Опис алгоритму:\n", "subheader")
        text.insert(tk.END, "Алгоритм групування мікросервісів базується на задачі про упаковку множинного рюкзака (Multiple Knapsack Problem) і має на меті сформувати стабільні групи мікросервісів з мінімальним коефіцієнтом варіації.\n\n")
        
        text.insert(tk.END, "Основні етапи алгоритму:\n", "subheader")
        text.insert(tk.END, "1. Спроба групування оригінальних мікросервісів:\n")
        text.insert(tk.END, "   • Спочатку алгоритм намагається сформувати групи по 2 мікросервіси з найкращою стабільністю\n")
        text.insert(tk.END, "   • Якщо залишаються негруповані мікросервіси, алгоритм намагається сформувати групи по 3 мікросервіси\n")
        text.insert(tk.END, "   • Процес продовжується до досягнення максимального розміру групи\n\n")
        
        text.insert(tk.END, "2. Розділення незгрупованих мікросервісів на базові та пікові компоненти:\n")
        text.insert(tk.END, "   • Мікросервіси, які не вдалося згрупувати, розділяються на базові та пікові компоненти\n")
        text.insert(tk.END, "   • Базовий компонент представляє стабільне навантаження мікросервісу\n")
        text.insert(tk.END, "   • Піковий компонент представляє нестабільні піки навантаження\n\n")
        
        text.insert(tk.END, "3. Групування базових компонентів:\n")
        text.insert(tk.END, "   • Алгоритм намагається сформувати групи з базових компонентів, використовуючи той самий підхід, що й для оригінальних мікросервісів\n\n")
        
        text.insert(tk.END, "4. Обробка пікових компонентів:\n")
        text.insert(tk.END, "   • Пікові компоненти додаються як окремі групи або об'єднуються з іншими піковими компонентами, якщо це покращує стабільність\n\n")
        
        text.insert(tk.END, "Оцінка стабільності групи:\n", "subheader")
        text.insert(tk.END, "Стабільність групи оцінюється за допомогою коефіцієнта варіації, який обчислюється за формулою:\n")
        text.insert(tk.END, "CV = (σ / μ) * 100%\n")
        text.insert(tk.END, "де:\n")
        text.insert(tk.END, "• σ - стандартне відхилення загального навантаження групи\n")
        text.insert(tk.END, "• μ - середнє значення загального навантаження групи\n\n")
        
        text.insert(tk.END, "Чим менший коефіцієнт варіації, тим стабільніша група. Групи з коефіцієнтом варіації вище заданого порогу вважаються нестабільними і не формуються.\n\n")
        
        text.insert(tk.END, "Переваги алгоритму:\n", "subheader")
        text.insert(tk.END, "• Формування стабільних груп мікросервісів з мінімальним коефіцієнтом варіації\n")
        text.insert(tk.END, "• Можливість розділення мікросервісів на базові та пікові компоненти для покращення стабільності\n")
        text.insert(tk.END, "• Гнучкість у виборі параметрів групування (максимальний розмір групи, коефіцієнт варіації)\n")
        text.insert(tk.END, "• Можливість аналізу різних типів метрик (CPU, RAM, CHANNEL)\n\n")
        
        # Налаштування стилів тексту
        text.tag_configure("header", font=("TkDefaultFont", 14, "bold"))
        text.tag_configure("subheader", font=("TkDefaultFont", 12, "bold"))
        
        # Заборона редагування тексту
        text.config(state=tk.DISABLED)

# Запуск додатку
if __name__ == "__main__":
    root = tk.Tk()
    app = MicroserviceGroupingApp(root)
    app.run() 