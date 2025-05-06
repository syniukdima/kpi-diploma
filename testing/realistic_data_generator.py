import random
import numpy as np
import json
import os

def generate_constant_service(base_load=2, variation=0.5):
    """
    Generates a microservice with almost constant load.
    
    Args:
        base_load: Base load value
        variation: Maximum deviation from base load
        
    Returns:
        List of 24 load values
    """
    return [max(1, round(random.uniform(base_load - variation, base_load + variation), 1)) for _ in range(24)]

def generate_day_service(min_load=1, max_load=5):
    """
    Generates a microservice with daytime load pattern.
    Peak hours: 9-18 (working day)
    
    Returns:
        List of 24 load values
    """
    loads = []
    for hour in range(24):
        if 0 <= hour < 6:  # Night minimum
            load = random.uniform(min_load, min_load + 0.5)
        elif 6 <= hour < 9:  # Morning increase
            progress = (hour - 6) / 3
            load = min_load + progress * (max_load - min_load)
        elif 9 <= hour < 18:  # Day peak
            load = random.uniform(max_load - 1, max_load)
        elif 18 <= hour < 22:  # Evening decrease
            progress = (hour - 18) / 4
            load = max_load - progress * (max_load - min_load)
        else:  # Night decrease
            load = random.uniform(min_load, min_load + 1)
        loads.append(max(1, round(load, 1)))
    return loads

def generate_night_service(min_load=1, max_load=5):
    """
    Generates a microservice with night load pattern.
    Peak hours: 20-4 (evening and night)
    
    Returns:
        List of 24 load values
    """
    loads = []
    for hour in range(24):
        if 0 <= hour < 4:  # Night peak
            load = random.uniform(max_load - 1, max_load)
        elif 4 <= hour < 8:  # Morning decrease
            progress = (hour - 4) / 4
            load = max_load - progress * (max_load - min_load)
        elif 8 <= hour < 16:  # Day minimum
            load = random.uniform(min_load, min_load + 1)
        elif 16 <= hour < 20:  # Evening increase
            progress = (hour - 16) / 4
            load = min_load + progress * (max_load - min_load)
        else:  # Night peak
            load = random.uniform(max_load - 1, max_load)
        loads.append(max(1, round(load, 1)))
    return loads

def generate_peak_service(base_load=1, peak_load=5, peak_hour=None):
    """
    Generates a microservice with a sharp peak load at a specific hour.
    
    Args:
        base_load: Base load value
        peak_load: Peak load value
        peak_hour: Hour of the peak (if None, chosen randomly)
        
    Returns:
        List of 24 load values
    """
    if peak_hour is None:
        peak_hour = random.randint(0, 23)
    
    loads = []
    for hour in range(24):
        if hour == peak_hour:
            load = peak_load
        elif abs(hour - peak_hour) == 1 or abs(hour - peak_hour) == 23:  # Adjacent hours (with cyclicity)
            load = random.uniform(base_load + 1, peak_load - 1)
        else:
            load = random.uniform(base_load, base_load + 1)
        loads.append(max(1, round(load, 1)))
    return loads

def generate_complementary_service(service):
    """
    Generates a microservice complementary to the given one.
    
    Args:
        service: List of 24 load values
        
    Returns:
        List of 24 load values complementary to the input
    """
    max_load = max(service)
    min_load = min(service)
    
    # Create complementary load: if original is high, result is low and vice versa
    return [max(1, round(max_load + min_load - load, 1)) for load in service]

def generate_microservice_dataset(num_services, output_file=None):
    """
    Generates a set of microservices with realistic load patterns.
    
    Args:
        num_services: Number of microservices
        output_file: File to save results (if None, only returns data)
        
    Returns:
        List of lists with 24 load values
    """
    # Distribution of microservice types
    constant_ratio = 0.2  # 20% constant
    day_ratio = 0.3       # 30% day-time
    night_ratio = 0.2     # 20% night-time
    peak_ratio = 0.1      # 10% peak
    complementary_ratio = 0.2  # 20% complementary
    
    services = []
    
    # Generate constant microservices
    constant_count = int(num_services * constant_ratio)
    for _ in range(constant_count):
        base_load = random.uniform(1.5, 4)
        services.append(generate_constant_service(base_load=base_load))
    
    # Generate day-time microservices
    day_count = int(num_services * day_ratio)
    for _ in range(day_count):
        services.append(generate_day_service())
    
    # Generate night-time microservices
    night_count = int(num_services * night_ratio)
    for _ in range(night_count):
        services.append(generate_night_service())
    
    # Generate peak microservices
    peak_count = int(num_services * peak_ratio)
    peak_hours = random.sample(range(24), min(peak_count, 24))
    for i in range(peak_count):
        peak_hour = peak_hours[i % len(peak_hours)]
        services.append(generate_peak_service(peak_hour=peak_hour))
    
    # Generate complementary microservices
    complementary_count = int(num_services * complementary_ratio)
    source_indices = random.sample(range(len(services)), min(complementary_count, len(services)))
    for idx in source_indices:
        services.append(generate_complementary_service(services[idx]))
    
    # Add random microservices if needed
    while len(services) < num_services:
        service_type = random.choice(["constant", "day", "night", "peak"])
        if service_type == "constant":
            services.append(generate_constant_service())
        elif service_type == "day":
            services.append(generate_day_service())
        elif service_type == "night":
            services.append(generate_night_service())
        else:
            services.append(generate_peak_service())
    
    # Round values to one decimal place
    services = [[round(value, 1) for value in service] for service in services]
    
    # Save to file if needed
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(services, f, indent=2)
        print(f"Data saved to file {output_file}")
    
    return services

def plot_services(services, num_samples=5, output_file=None):
    """
    Visualizes the load of selected microservices.
    
    Args:
        services: List of lists with 24 load values
        num_samples: Number of microservices to display
        output_file: File to save the plot
    """
    try:
        import matplotlib.pyplot as plt
        
        # Select random microservices for visualization
        sample_indices = random.sample(range(len(services)), min(num_samples, len(services)))
        
        plt.figure(figsize=(12, 6))
        hours = list(range(24))
        
        for idx in sample_indices:
            plt.plot(hours, services[idx], label=f"Microservice {idx}")
        
        plt.xlabel("Hour of day")
        plt.ylabel("Load")
        plt.title("Daily load patterns of microservices")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(range(0, 24, 2))
        plt.xlim(0, 23)
        plt.legend()
        
        if output_file:
            plt.savefig(output_file)
            print(f"Plot saved to file {output_file}")
        else:
            plt.show()
    
    except ImportError:
        print("Matplotlib library is required for visualization")

if __name__ == "__main__":
    # Example usage
    # Generate 50 microservices and save to file
    services = generate_microservice_dataset(50, "testing/microservices_data.json")
    
    # Visualize sample microservices
    try:
        plot_services(services, num_samples=8, output_file="testing/microservices_patterns.png")
    except Exception as e:
        print(f"Visualization failed: {e}")
    
    # Demonstration of different types
    print("\nExamples of different microservice types:")
    print("Constant:     ", generate_constant_service())
    print("Day-time:     ", generate_day_service())
    print("Night-time:   ", generate_night_service())
    print("Peak:         ", generate_peak_service())
    
    # Demonstration of complementary pairs
    original = generate_day_service()
    complementary = generate_complementary_service(original)
    
    print("\nExample of complementary pair:")
    print("Original:     ", original)
    print("Complementary:", complementary)
    print("Sum:          ", [round(a + b, 1) for a, b in zip(original, complementary)]) 