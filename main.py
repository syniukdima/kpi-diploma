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

def form_multiple_knapsack_groups(microservices, num_knapsacks=None, max_capacity=None):
    """
    Forms groups of microservices using the multiple knapsack problem approach.
    
    Args:
        microservices: List of time series for microservice loads
        num_knapsacks: Number of knapsacks (groups) to form. If None, it's determined automatically
        max_capacity: Maximum capacity for each knapsack. If None, it's calculated based on average load
    
    Returns:
        Tuple of (groups, group_services, slot_sums)
        - groups: List of groups, where each group contains time series of microservices
        - group_services: List of microservice indices in each group
        - slot_sums: List of total loads by time slots for each group
    """
    n = len(microservices)
    
    # If num_knapsacks is not specified, make a reasonable estimate
    if num_knapsacks is None:
        num_knapsacks = max(1, n // 3)  # Default: aim for ~3 microservices per group
    
    # Calculate weights and values for each microservice
    weights = []  # Weight = average load of a microservice
    values = []   # Value = inverse of coefficient of variation (stability value)
    
    for service in microservices:
        # Weight is the average load of the microservice
        weights.append(sum(service) / len(service))
        
        # Value is inversely proportional to the coefficient of variation
        # More stable services have higher value
        stability = calculate_stability([service])
        if stability == 0:
            values.append(float('inf'))
        else:
            values.append(100.0 / stability)  # Higher value for more stable services
    
    # Calculate knapsack capacities
    total_weight = sum(weights)
    
    if max_capacity is None:
        # Set each knapsack's capacity to be slightly more than the average required
        avg_weight_per_knapsack = total_weight / num_knapsacks
        max_capacity = avg_weight_per_knapsack * 1.2  # Add 20% buffer
    
    knapsack_capacities = [max_capacity] * num_knapsacks
    
    # Solve the multiple knapsack problem
    assignments = solve_multiple_knapsack(weights, values, knapsack_capacities, microservices)
    
    # Convert the assignments to the expected output format
    groups = []
    group_services = []
    slot_sums_per_group = []
    
    for assignment in assignments:
        if assignment:  # Skip empty assignments
            group = [microservices[idx] for idx in assignment]
            groups.append(group)
            group_services.append(assignment)
            slot_sums_per_group.append(calculate_load_sum(group))
    
    return groups, group_services, slot_sums_per_group

def solve_multiple_knapsack(weights, values, capacities, microservices):
    """
    Solves the multiple knapsack problem using a Worst-Fit greedy approach.
    
    Args:
        weights: List of item weights
        values: List of item values
        capacities: List of knapsack capacities
        microservices: Original microservices data (for stability calculation)
        
    Returns:
        List of lists, where each inner list contains indices of items assigned to a knapsack
    """
    n = len(weights)  # Number of items
    m = len(capacities)  # Number of knapsacks
    
    # Sort items by value/weight ratio (efficiency) in descending order
    items = list(range(n))
    items.sort(key=lambda i: values[i] / weights[i] if weights[i] > 0 else float('inf'), reverse=True)
    
    # Initialize knapsacks
    knapsacks = [[] for _ in range(m)]
    remaining_capacities = capacities.copy()
    
    # First pass: assign items to knapsacks using Worst-Fit strategy
    for item in items:
        # Find the best knapsack for this item - the one with maximum remaining capacity
        best_knapsack = -1
        max_remaining = -1
        
        for j in range(m):
            if weights[item] <= remaining_capacities[j]:
                if best_knapsack == -1 or remaining_capacities[j] > max_remaining:
                    max_remaining = remaining_capacities[j]
                    best_knapsack = j
        
        # If a suitable knapsack is found, add the item
        if best_knapsack != -1:
            knapsacks[best_knapsack].append(item)
            remaining_capacities[best_knapsack] -= weights[item]
    
    # Second pass: try to swap items between knapsacks to improve stability
    improved = True
    while improved:
        improved = False
        
        for i in range(m):
            for j in range(i+1, m):
                # Skip if either knapsack is empty
                if not knapsacks[i] or not knapsacks[j]:
                    continue
                
                # Try to swap items between knapsacks i and j
                for item_i_idx, item_i in enumerate(knapsacks[i]):
                    for item_j_idx, item_j in enumerate(knapsacks[j]):
                        # Check if swap is feasible (capacity constraints)
                        weight_diff = weights[item_j] - weights[item_i]
                        if (remaining_capacities[i] >= weight_diff and 
                            remaining_capacities[j] >= -weight_diff):
                            
                            # Check if swap improves stability
                            # Make copies of the knapsacks for testing
                            test_knapsack_i = knapsacks[i].copy()
                            test_knapsack_j = knapsacks[j].copy()
                            
                            # Swap items
                            test_knapsack_i[item_i_idx] = item_j
                            test_knapsack_j[item_j_idx] = item_i
                            
                            # Calculate stability before and after swap
                            stability_before = (
                                calculate_stability([microservices[idx] for idx in knapsacks[i]]) +
                                calculate_stability([microservices[idx] for idx in knapsacks[j]])
                            )
                            
                            stability_after = (
                                calculate_stability([microservices[idx] for idx in test_knapsack_i]) +
                                calculate_stability([microservices[idx] for idx in test_knapsack_j])
                            )
                            
                            # If stability improves, perform the swap
                            if stability_after < stability_before:
                                knapsacks[i][item_i_idx] = item_j
                                knapsacks[j][item_j_idx] = item_i
                                
                                # Update remaining capacities
                                remaining_capacities[i] -= weight_diff
                                remaining_capacities[j] += weight_diff
                                
                                improved = True
                                break  # Break inner loop
                    
                    if improved:
                        break  # Break outer loop
    
    return knapsacks

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
    # Example with more microservices (6 time slots)
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
        # Set num_knapsacks explicitly to create multiple groups
        groups, group_services, slot_sums = form_multiple_knapsack_groups(microservices, num_knapsacks=3)
        print_results(groups, group_services, slot_sums)
    except ValueError as e:
        print(f"Error: {e}")
    
    

