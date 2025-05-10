import psutil
import json
import time
import copy
import random
from datetime import datetime, timedelta

# === ПАРАМЕТРИ ===
interval = 5                     # сек між зняттями метрик
duration = 24 * 5                # тривалість одного періоду збору (сек)
samples = int(duration // interval)
num_services = 100              # кількість мікросервісів
start_date = datetime(2025, 5, 10)
runs = 7                        # кількість днів (файлів)

for run in range(runs):
    current_date = start_date - timedelta(days=run)
    date_str = current_date.strftime("%Y-%m-%d")
    output_file = f"simulated_services_{date_str}.json"

    print(f"Collecting data for: {date_str}")

    # === КРОК 1: Збір базових метрик ===
    base_metrics = []
    net_before = psutil.net_io_counters()

    for _ in range(samples):
        cpu = psutil.cpu_percent(interval=0.1)
        mem_used = psutil.virtual_memory().used / (1024 * 1024)  # MB

        net_after = psutil.net_io_counters()
        net_in = (net_after.bytes_recv - net_before.bytes_recv) / 1024  # KB
        net_out = (net_after.bytes_sent - net_before.bytes_sent) / 1024
        net_before = net_after

        base_metrics.append({
            "date": date_str,
            "time": "00:00",
            "cpu": round(cpu, 2),
            "memory_used_mb": round(mem_used, 2),
            "net_in_kb": round(net_in, 2),
            "net_out_kb": round(net_out, 2)
        })

        time.sleep(interval - 0.1)

    # === КРОК 2: Генерація симульованих мікросервісів ===
    simulated_services = {}

    for i in range(1, num_services + 1):
        service_name = f"service_{i}"
        noisy_series = []

        for entry in base_metrics:
            noisy_entry = copy.deepcopy(entry)

            # Додаємо шум (±10%)
            for key in ["cpu", "memory_used_mb", "net_in_kb", "net_out_kb"]:
                base_value = noisy_entry[key]
                noise = random.uniform(-0.1, 0.1) * base_value
                noisy_entry[key] = round(base_value + noise, 2)

            noisy_series.append(noisy_entry)

        simulated_services[service_name] = noisy_series

    # === КРОК 3: Запис у файл ===
    with open(output_file, "w") as f:
        json.dump(simulated_services, f, indent=2)

    print(f"Saved: {output_file}")
