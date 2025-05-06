def distribute_items_to_knapsacks(item_arrays, num_knapsacks, max_deviation_percent=None):
    """
    Distributes numbers from several arrays into knapsacks to achieve approximately equal sum in each knapsack.
    
    Args:
        item_arrays: List of number arrays to distribute
        num_knapsacks: Number of knapsacks for distribution
        max_deviation_percent: Maximum allowed deviation from ideal weight in percentage
                              (e.g., 10 means ±10% from ideal weight). If None, no constraint is applied.
    
    Returns:
        List of knapsacks, where each knapsack is a list of numbers
        
    Raises:
        ValueError: If no valid solution can be found within the given constraint
    """
    # Combine all numbers into one array
    all_items = []
    for array in item_arrays:
        all_items.extend(array)
    
    # Calculate ideal weight per knapsack
    total_weight = sum(all_items)
    ideal_weight = total_weight / num_knapsacks
    
    # Sort numbers in descending order for better balancing
    all_items.sort(reverse=True)
    
    # Initialize knapsacks
    knapsacks = [[] for _ in range(num_knapsacks)]
    knapsack_sums = [0] * num_knapsacks
    
    # Distribute each number to the knapsack with the lowest current sum
    for item in all_items:
        # Find the knapsack with the minimum sum
        min_knapsack_index = knapsack_sums.index(min(knapsack_sums))
        
        # Add the number to this knapsack
        knapsacks[min_knapsack_index].append(item)
        knapsack_sums[min_knapsack_index] += item
    
    # Check if solution meets the deviation constraint (if provided)
    if max_deviation_percent is not None:
        min_allowed = ideal_weight * (1 - max_deviation_percent / 100)
        max_allowed = ideal_weight * (1 + max_deviation_percent / 100)
        
        # Check if any knapsack is outside the allowed range
        for knapsack_sum in knapsack_sums:
            if knapsack_sum < min_allowed or knapsack_sum > max_allowed:
                raise ValueError(
                    f"Could not find a solution within ±{max_deviation_percent}% of ideal weight ({ideal_weight:.2f}).\n"
                    f"Knapsack sums: {knapsack_sums}\n"
                    f"Allowed range: {min_allowed:.2f} to {max_allowed:.2f}\n"
                    f"Try increasing the deviation percentage or use a different algorithm."
                )
    
    return knapsacks

def distribute_with_percentage_constraint(item_arrays, num_knapsacks, max_deviation_percent):
    """
    Distributes items with a percentage-based constraint on deviation from ideal weight.
    
    Args:
        item_arrays: List of number arrays to distribute
        num_knapsacks: Number of knapsacks for distribution
        max_deviation_percent: Maximum allowed deviation from ideal weight in percentage
                              (e.g., 10 means ±10% from ideal weight)
    
    Returns:
        Tuple of (knapsacks, success_flag)
        - knapsacks: The distribution of items
        - success_flag: True if the solution meets the constraint, False otherwise
    
    Raises:
        ValueError: If no valid solution can be found within the given constraint
    """
    # Combine all numbers into one array
    all_items = []
    for array in item_arrays:
        all_items.extend(array)
    
    # Calculate ideal weight per knapsack
    total_weight = sum(all_items)
    ideal_weight = total_weight / num_knapsacks
    
    # Calculate min and max allowed weight based on deviation percentage
    min_allowed = ideal_weight * (1 - max_deviation_percent / 100)
    max_allowed = ideal_weight * (1 + max_deviation_percent / 100)
    
    # Try normal distribution first
    knapsacks = distribute_items_to_knapsacks([all_items], num_knapsacks)
    
    # Check if the solution meets the constraint
    within_constraint = True
    for knapsack in knapsacks:
        knapsack_sum = sum(knapsack)
        if knapsack_sum < min_allowed or knapsack_sum > max_allowed:
            within_constraint = False
            break
    
    if not within_constraint:
        raise ValueError(
            f"Could not find a solution within ±{max_deviation_percent}% of ideal weight ({ideal_weight:.2f}). "
            f"Try increasing the deviation percentage or use a different algorithm."
        )
    
    return knapsacks

def print_results(knapsacks):
    """
    Prints the distribution results of the knapsacks.
    
    Args:
        knapsacks: List of knapsacks with numbers
    """
    print("Distribution results:")
    total_sum = 0
    
    for i, knapsack in enumerate(knapsacks):
        knapsack_sum = sum(knapsack)
        total_sum += knapsack_sum
        print(f"Knapsack {i+1}: {knapsack} - Sum: {knapsack_sum}")
    
    average_sum = total_sum / len(knapsacks)
    print(f"\nAverage sum per knapsack: {average_sum:.2f}")
    
    # Calculate deviation from the average sum
    deviations = [abs(sum(knapsack) - average_sum) for knapsack in knapsacks]
    average_deviation = sum(deviations) / len(deviations)
    max_deviation = max(deviations)
    
    print(f"Average deviation: {average_deviation:.2f}")
    print(f"Maximum deviation: {max_deviation:.2f}")
    
    # Calculate percentage deviation
    percentage_deviations = [abs(sum(knapsack) - average_sum) / average_sum * 100 for knapsack in knapsacks]
    average_percentage_deviation = sum(percentage_deviations) / len(percentage_deviations)
    max_percentage_deviation = max(percentage_deviations)
    
    print(f"Average percentage deviation: {average_percentage_deviation:.2f}%")
    print(f"Maximum percentage deviation: {max_percentage_deviation:.2f}%")

# Example usage
if __name__ == "__main__":
    array1 = [10, 14, 8, 12]
    array2 = [7, 9, 1, 14]
    array3 = [6, 13, 5, 4]
    array4 = [6, 13, 5, 4]
    
    item_arrays = [array1, array2, array3, array4]
    num_knapsacks = 4

    try:
        grouped_knapsacks = distribute_items_to_knapsacks(item_arrays, num_knapsacks, max_deviation_percent=10)
        print_results(grouped_knapsacks)
    except ValueError as e:
        print(f"Error: {e}")

