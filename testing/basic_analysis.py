import sys
import os

# Add the project root directory to the module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import random

def generate_random_microservices(num_services, time_slots, min_load=1, max_load=5):
    """
    Generates random microservices with given parameters.
    """
    return [
        [random.randint(min_load, max_load) for _ in range(time_slots)]
        for _ in range(num_services)
    ]

def generate_complementary_microservices(num_services, time_slots, min_load=1, max_load=5):
    """
    Generates microservices with complementary load patterns.
    """
    services = []
    
    # Create pairs of microservices with complementary load
    for i in range(num_services // 2):
        service1 = [random.randint(min_load, max_load) for _ in range(time_slots)]
        service2 = [max_load + min_load - service1[j] for j in range(time_slots)]
        services.append(service1)
        services.append(service2)
    
    # If the number of microservices is odd, add one more random microservice
    if num_services % 2 == 1:
        services.append([random.randint(min_load, max_load) for _ in range(time_slots)])
    
    return services

def print_test_results(test_name, microservices, groups, group_services, slot_sums):
    """
    Prints test results in a formatted way.
    """
    print(f"\n{'=' * 60}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 60}")
    
    print("Input data:")
    for i, service in enumerate(microservices):
        print(f"Microservice {i}: {service}")
    
    print("\nGroup distribution results:")
    
    group_cvs = []
    
    for i, (group, service_indices, sums) in enumerate(zip(groups, group_services, slot_sums)):
        # Calculate statistics
        mean = sum(sums) / len(sums)
        variance = sum((x - mean) ** 2 for x in sums) / len(sums)
        std_dev = variance ** 0.5
        cv = (std_dev / mean) * 100 if mean > 0 else float('inf')
        group_cvs.append(cv)
        
        print(f"\nGroup {i+1}:")
        print(f"  Microservices: {service_indices}")
        print(f"  Total load by time slots: {sums}")
        print(f"  Coefficient of variation: {cv:.2f}%")
    
    # Overall statistics
    avg_cv = sum(group_cvs) / len(group_cvs) if group_cvs else 0
    
    print("\nOverall statistics:")
    print(f"  Number of groups: {len(groups)}")
    print(f"  Total number of microservices: {sum(len(g) for g in group_services)}")
    print(f"  Average coefficient of variation: {avg_cv:.2f}%")
    print(f"  Minimum coefficient of variation: {min(group_cvs):.2f}% (Group {group_cvs.index(min(group_cvs))+1})")
    print(f"  Maximum coefficient of variation: {max(group_cvs):.2f}% (Group {group_cvs.index(max(group_cvs))+1})")
    
    return group_cvs, avg_cv

def analyze_algorithm_performance():
    """
    Analyzes algorithm performance on various test cases.
    """
    test_results = []
    
    # Test 1: Regular test with 6 microservices, 4 time slots
    microservices = [
        [1, 2, 3, 4],  # Microservice 0
        [4, 3, 2, 1],  # Microservice 1
        [2, 2, 2, 2],  # Microservice 2
        [3, 1, 4, 2],  # Microservice 3
        [2, 4, 1, 3],  # Microservice 4
        [3, 2, 3, 2],  # Microservice 5
    ]
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Basic test (6 microservices, 4 time slots)", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Basic test", avg_cv))
    
    # Test 2: Microservices with perfectly complementary loads
    microservices = [
        [1, 5, 2, 4],  # Microservice 0
        [5, 1, 4, 2],  # Microservice 1 (complementary to 0)
        [3, 2, 5, 1],  # Microservice 2
        [3, 4, 1, 5],  # Microservice 3 (complementary to 2)
        [2, 2, 3, 4],  # Microservice 4
        [4, 4, 3, 2],  # Microservice 5 (complementary to 4)
    ]
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Complementary microservices", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Complementary", avg_cv))
    
    # Test 3: Random microservices
    random.seed(42)  # for reproducibility
    microservices = generate_random_microservices(30, 6)
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Random microservices (30 items, 6 time slots)", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Random", avg_cv))
    
    # Test 4: Generated complementary microservices
    microservices = generate_complementary_microservices(8, 6)
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Generated complementary microservices (8 items, 6 time slots)", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Generated compl.", avg_cv))
    
    # Test 5: Realistic scenario with different types of microservices
    # Combine different load patterns
    microservices = []
    # Add a few with stable load
    microservices.extend([[3, 3, 3, 3, 3, 3], [2, 2, 2, 2, 2, 2]])
    # Add a few with slowly changing load
    microservices.extend([[1, 2, 2, 3, 3, 2], [3, 2, 2, 1, 1, 2]])
    # Add a few with moderate changes
    microservices.extend([[2, 3, 4, 3, 2, 1], [1, 2, 3, 4, 3, 2]])
    # Add a few with minor fluctuations
    microservices.extend([[2, 3, 2, 3, 2, 3], [3, 2, 3, 2, 3, 2]])
    
    groups, group_services, slot_sums = main.form_stable_groups(microservices)
    cvs, avg_cv = print_test_results("Realistic scenario with different load patterns", 
                                   microservices, groups, group_services, slot_sums)
    test_results.append(("Realistic", avg_cv))
    
    print("\nComparison of test results:")
    for test_name, avg_cv in test_results:
        print(f"{test_name}: average coefficient of variation = {avg_cv:.2f}%")
    
    try:
        # Try to save results to a text file
        with open('testing/test_results_summary.txt', 'w', encoding='utf-8') as f:
            f.write("Comparison of test results:\n")
            for test_name, avg_cv in test_results:
                f.write(f"{test_name}: average coefficient of variation = {avg_cv:.2f}%\n")
        print("\nResults saved to file 'testing/test_results_summary.txt'")
    except Exception as e:
        print(f"\nError saving results: {e}")

if __name__ == "__main__":
    analyze_algorithm_performance() 