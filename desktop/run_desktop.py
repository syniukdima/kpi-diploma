import sys
import os
import tkinter as tk

# Додавання шляху до спільних модулів
sys.path.append(os.path.abspath(".."))

# Імпорт і запуск десктопного додатку
from ui import MicroserviceGroupingApp

if __name__ == "__main__":
    root = tk.Tk()
    app = MicroserviceGroupingApp(root)
    app.run() 