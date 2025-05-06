def distribute_items_to_knapsacks(item_arrays, num_knapsacks):
    """
    Distributes numbers from several arrays into knapsacks to achieve approximately equal sum in each knapsack.
    
    Args:
        item_arrays: List of number arrays to distribute
        num_knapsacks: Number of knapsacks for distribution
    
    Returns:
        List of knapsacks, where each knapsack is a list of numbers
    """
    # Combine all numbers into one array
    all_items = []
    for array in item_arrays:
        all_items.extend(array)
    
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

# Example usage
if __name__ == "__main__":
    array1 = [10, 14, 8, 12]
    array2 = [7, 9, 1, 14]
    array3 = [6, 13, 5, 4]
    array4 = [6, 13, 5, 4]
    
    item_arrays = [array1, array2, array3, array4]
    num_knapsacks = 4
    
    knapsacks = distribute_items_to_knapsacks(item_arrays, num_knapsacks)
    print_results(knapsacks)
