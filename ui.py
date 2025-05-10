import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
from typing import List, Dict, Any, Tuple

from db_input import DBInput
from group_finder import form_multiple_knapsack_groups
from visualization import Visualizer

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
        
        # Поріг стабільності
        ttk.Label(params_frame, text="Поріг стабільності (%):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.stability_threshold_var = tk.DoubleVar(value=20.0)
        stability_threshold_spin = ttk.Spinbox(params_frame, from_=5.0, to=50.0, increment=0.5, 
                                             textvariable=self.stability_threshold_var, width=5)
        stability_threshold_spin.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Кнопка запуску групування
        self.run_button = ttk.Button(params_frame, text="Запустити групування", command=self._run_grouping)
        self.run_button.grid(row=1, column=5, sticky=tk.E, padx=5, pady=5)
        
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
        
        self.notebook.add(self.tab_microservices, text="Мікросервіси")
        self.notebook.add(self.tab_group_load, text="Навантаження груп")
        self.notebook.add(self.tab_stability, text="Стабільність")
        self.notebook.add(self.tab_statistics, text="Статистика")
        self.notebook.add(self.tab_base_peak, text="Базові/пікові компоненти")
        
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
        
        for group in self.groups:
            # Обчислення загального навантаження групи
            time_slots = len(group[0]) if group else 0
            total_load = [0] * time_slots
            
            for service in group:
                for t in range(time_slots):
                    total_load[t] += service[t]
            
            mean_loads.append(sum(total_load) / len(total_load) if total_load else 0)
            peak_loads.append(max(total_load) if total_load else 0)
        
        # Додавання статистики в текстове поле
        stats_text.insert(tk.END, f"Загальна статистика:\n")
        stats_text.insert(tk.END, f"- Кількість груп: {len(self.groups)}\n")
        stats_text.insert(tk.END, f"- Кількість мікросервісів: {len(self.microservices)}\n")
        stats_text.insert(tk.END, f"- Тип метрики: {self.metric_var.get()}\n")
        stats_text.insert(tk.END, f"- Дата: {self.date_var.get()}\n")
        stats_text.insert(tk.END, f"- Час: {self.time_var.get()}\n")
        stats_text.insert(tk.END, f"- Максимальний розмір групи: {self.group_size_var.get()}\n")
        stats_text.insert(tk.END, f"- Поріг стабільності: {self.stability_threshold_var.get()}%\n\n")
        
        stats_text.insert(tk.END, "Статистика по групах:\n")
        stats_text.insert(tk.END, "-" * 50 + "\n")
        
        for i, (size, mean, peak) in enumerate(zip(group_sizes, mean_loads, peak_loads)):
            stats_text.insert(tk.END, f"Група {i+1}:\n")
            stats_text.insert(tk.END, f"  Кількість мікросервісів: {size}\n")
            stats_text.insert(tk.END, f"  Середнє навантаження: {mean:.2f}\n")
            stats_text.insert(tk.END, f"  Пікове навантаження: {peak:.2f}\n")
            
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
        from split_extreme_loads import split_microservice_load
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
        except:
            pass

# Запуск додатку
if __name__ == "__main__":
    root = tk.Tk()
    app = MicroserviceGroupingApp(root)
    app.run() 