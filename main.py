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

def generate_stable_groups(available_indices, microservices, group_size, stability_threshold):
    """
    Generates all possible combinations of the given size from available microservices,
    filters by stability threshold, and sorts by CV (ascending).
    
    Args:
        available_indices: List of available microservice indices
        microservices: List of all microservices
        group_size: Size of groups to generate
        stability_threshold: Maximum CV value to consider stable
        
    Returns:
        List of tuples (group, indices, cv) sorted by cv ascending
    """
    from itertools import combinations
    
    candidate_groups = []
    
    # Generate all combinations of current group size from available microservices
    for indices in combinations(range(len(available_indices)), group_size):
        # Map to actual microservice indices
        actual_indices = [available_indices[i] for i in indices]
        # Get the microservices for these indices
        group = [microservices[idx] for idx in actual_indices]
        
        # Calculate stability for this group
        cv = calculate_stability(group)
        
        # If stability is good enough, add to candidates
        if cv < stability_threshold:
            candidate_groups.append((group, actual_indices, cv))
    
    # Sort candidate groups by stability (lowest CV first)
    return sorted(candidate_groups, key=lambda x: x[2])

def is_group_available(group_indices, used_indices_set):
    """
    Checks if all indices in the group are still available (not used).
    
    Args:
        group_indices: List of indices to check
        used_indices_set: Set of already used indices
        
    Returns:
        True if all indices are available, False otherwise
    """
    return not any(idx in used_indices_set for idx in group_indices)

def form_multiple_knapsack_groups(microservices, num_knapsacks=None, max_group_size=4, stability_threshold=20.0):
    """
    Forms groups of microservices using an incremental approach:
    1. First try to group by 2, keeping pairs with good stability
    2. Then try to group remaining services by 3, and so on
    
    Args:
        microservices: List of time series for microservice loads
        num_knapsacks: Number of knapsacks (groups) to form. If None, it's determined automatically
        max_group_size: Maximum number of elements in a group to try (default: 4)
        stability_threshold: Threshold for coefficient of variation (default: 20.0%)
    
    Returns:
        Tuple of (groups, group_services, slot_sums)
        - groups: List of groups, where each group contains time series of microservices
        - group_services: List of microservice indices in each group
        - slot_sums: List of total loads by time slots for each group
    """
    n = len(microservices)
    
    # Initialize final groups
    final_groups = []
    final_group_indices = []
    final_slot_sums = []
    
    # Keep track of which microservices are still available
    available_indices = list(range(n))
    
    # Iterate over group sizes from 2 to max_group_size
    for group_size in range(2, min(max_group_size + 1, n + 1)):
        print(f"\nTrying with group size: {group_size}")
        
        if len(available_indices) < group_size:
            print(f"  Not enough services left for group size {group_size}")
            break
        
        # Generate stable groups for current size
        candidate_groups = generate_stable_groups(
            available_indices, 
            microservices, 
            group_size, 
            stability_threshold
        )
        
        if not candidate_groups:
            print(f"  No stable groups found with size {group_size}")
            continue
        
        print(f"  Found {len(candidate_groups)} stable groups with size {group_size}")
        
        # Create set of all already used indices for quick lookup
        used_indices_set = set(idx for group in final_group_indices for idx in group)
        
        # Add stable groups to final groups
        for group, actual_indices, cv in candidate_groups:
            # Skip if any index is already used
            if not is_group_available(actual_indices, used_indices_set):
                continue
                
            # Add this group to final groups
            final_groups.append(group)
            final_group_indices.append(actual_indices)
            final_slot_sums.append(calculate_load_sum(group))
            
            # Update used indices set
            used_indices_set.update(actual_indices)
            
            print(f"  Added group with CV: {cv:.2f}% - {actual_indices}")
        
        # Update available indices by removing used ones
        available_indices = [idx for idx in available_indices if idx not in used_indices_set]
        
        print(f"  Remaining services: {len(available_indices)}")
        
        # If no more services left, we're done
        if not available_indices:
            break
    
    # Add any remaining microservices as single-element groups
    for idx in available_indices:
        final_groups.append([microservices[idx]])
        final_group_indices.append([idx])
        final_slot_sums.append(calculate_load_sum([microservices[idx]]))
        print(f"  Added single-element group: {idx}")
    
    # If we didn't form any groups, put each microservice in its own group
    if not final_groups:
        print("No groups formed. Creating single-element groups.")
        final_groups = [[microservice] for microservice in microservices]
        final_group_indices = [[i] for i in range(n)]
        final_slot_sums = [calculate_load_sum([microservice]) for microservice in microservices]
    
    return final_groups, final_group_indices, final_slot_sums

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
        # Set max_group_size to try different group sizes
        groups, group_services, slot_sums = form_multiple_knapsack_groups(
            microservices, 
            num_knapsacks=3,
            max_group_size=4
        )
        print_results(groups, group_services, slot_sums)
    except ValueError as e:
        print(f"Error: {e}")
    
    

