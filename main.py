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

def form_stable_groups(microservices):
    """
    Forms groups of microservices using a multiple knapsack algorithm
    with flexible target weight constraint.
    
    Args:
        microservices: List of time series for microservice loads
    
    Returns:
        Tuple of (groups, group_services, slot_sums)
        - groups: List of groups, where each group contains time series of microservices
        - group_services: List of microservice indices in each group
        - slot_sums: List of total loads by time slots for each group
    """
    n = len(microservices)
    time_slots = len(microservices[0])
    
    # Preparation of data for the knapsack
    service_indices = list(range(n))
    
    # Calculate the ideal target load - average across all microservices
    total_load = [0] * time_slots
    for service in microservices:
        for t in range(time_slots):
            total_load[t] += service[t]
    
    avg_load_per_slot = sum(total_load) / (time_slots * n)
    
    # Knapsack algorithm with flexible constraint
    groups = []  # Time series of microservices in each group
    group_services = []  # Indices of microservices in each group
    used = [False] * n
    slot_sums_per_group = []
    
    # Until all microservices are distributed
    while not all(used):
        # Initialize a new group
        current_group = []
        current_services = []
        current_load = [0] * time_slots
        
        # Find the best microservice to start a new group
        best_start_idx = -1
        best_start_stability = float('inf')
        
        for i in range(n):
            if not used[i]:
                test_stability = calculate_stability([microservices[i]])
                if test_stability < best_start_stability:
                    best_start_stability = test_stability
                    best_start_idx = i
        
        # Add the best starting microservice
        if best_start_idx != -1:
            current_group.append(microservices[best_start_idx])
            current_services.append(best_start_idx)
            used[best_start_idx] = True
            
            # Update the current load of the group
            for t in range(time_slots):
                current_load[t] += microservices[best_start_idx][t]
        
        # Try to add other microservices to achieve the target load
        improved = True
        while improved:
            improved = False
            
            best_service_idx = -1
            best_stability = calculate_stability(current_group)
            
            # Target load is the average load of all microservices multiplied by the current group size
            target_load = avg_load_per_slot * (len(current_services) + 1)
            
            # Loop through all unused microservices
            for i in range(n):
                if not used[i]:
                    # Add the microservice temporarily
                    test_group = current_group + [microservices[i]]
                    
                    # Calculate the new stability
                    test_stability = calculate_stability(test_group)
                    
                    # If stability improves, keep this microservice
                    if test_stability < best_stability:
                        best_stability = test_stability
                        best_service_idx = i
            
            # If a suitable microservice is found, add it to the group
            if best_service_idx != -1:
                current_group.append(microservices[best_service_idx])
                current_services.append(best_service_idx)
                used[best_service_idx] = True
                
                # Update the current load of the group
                for t in range(time_slots):
                    current_load[t] += microservices[best_service_idx][t]
                
                improved = True
            
            # If the group size has reached maximum or all microservices are used
            if len(current_services) >= n or all(used):
                break
        
        # Save the formed group
        if current_group:
            groups.append(current_group)
            group_services.append(current_services)
            slot_sums_per_group.append(current_load)
    
    return groups, group_services, slot_sums_per_group

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
    # Example with microservices (6 time slots)
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
        groups, group_services, slot_sums = form_stable_groups(microservices)
        print_results(groups, group_services, slot_sums)
    except ValueError as e:
        print(f"Error: {e}")
    
    

