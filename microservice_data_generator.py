import random
import numpy as np
import json
import os
import matplotlib.pyplot as plt

def generate_constant_service(base_load=5, variation=1):
    """
    Generates a microservice with almost constant load.
    
    Args:
        base_load: Base load value
        variation: Maximum deviation from base load
        
    Returns:
        List of 24 load values
    """
    return [max(1, min(10, random.randint(base_load - variation, base_load + variation))) for _ in range(24)]

def generate_day_service(min_load=1, max_load=10):
    """
    Generates a microservice with daytime load pattern.
    Peak hours: 9-18 (working day)
    
    Returns:
        List of 24 load values
    """
    loads = []
    for hour in range(24):
        if 0 <= hour < 6:  # Night minimum
            load = random.randint(min_load, min_load + 1)
        elif 6 <= hour < 9:  # Morning increase
            progress = (hour - 6) / 3
            load = min_load + int(progress * (max_load - min_load))
        elif 9 <= hour < 18:  # Day peak
            load = random.randint(max_load - 2, max_load)
        elif 18 <= hour < 22:  # Evening decrease
            progress = (hour - 18) / 4
            load = max_load - int(progress * (max_load - min_load))
        else:  # Night decrease
            load = random.randint(min_load, min_load + 2)
        loads.append(max(1, min(10, load)))
    return loads

def generate_night_service(min_load=1, max_load=10):
    """
    Generates a microservice with night load pattern.
    Peak hours: 20-4 (evening and night)
    
    Returns:
        List of 24 load values
    """
    loads = []
    for hour in range(24):
        if 0 <= hour < 4:  # Night peak
            load = random.randint(max_load - 2, max_load)
        elif 4 <= hour < 8:  # Morning decrease
            progress = (hour - 4) / 4
            load = max_load - int(progress * (max_load - min_load))
        elif 8 <= hour < 16:  # Day minimum
            load = random.randint(min_load, min_load + 2)
        elif 16 <= hour < 20:  # Evening increase
            progress = (hour - 16) / 4
            load = min_load + int(progress * (max_load - min_load))
        else:  # Night peak
            load = random.randint(max_load - 2, max_load)
        loads.append(max(1, min(10, load)))
    return loads

def generate_peak_service(base_load=1, peak_load=10, peak_hour=None):
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
            load = random.randint(base_load + 2, peak_load - 2)
        else:
            load = random.randint(base_load, base_load + 2)
        loads.append(max(1, min(10, load)))
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
    return [max(1, min(10, max_load + min_load - load)) for load in service]

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
        base_load = random.randint(3, 8)
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
    
    # Save to file if needed
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(services, f, indent=2)
        print(f"Data saved to file {output_file}")
    
    return services

if __name__ == "__main__":
    # Example usage
    # Generate 50 microservices and save to file
    services = generate_microservice_dataset(50, "microservices_data.json")