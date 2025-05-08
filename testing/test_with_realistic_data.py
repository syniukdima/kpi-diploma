import sys
import os

# Add the project root directory to the module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from testing import realistic_data_generator as rdg
import json

def test_realistic_workload(num_services=50, generate_new_data=True, input_file="testing/realistic_data.json"):
    """
    Tests the algorithm on realistic microservice data with 24 time slots
    
    Args:
        num_services: Number of microservices to generate
        generate_new_data: If True, generates new data, otherwise loads from file
        input_file: File for saving/loading data
    """
    print("\n" + "="*80)
    print("TESTING ON REALISTIC DATA WITH 24 TIME SLOTS")
    print("="*80)
    
    if generate_new_data:
        # Generate a set of microservices
        print(f"Generating {num_services} microservices with realistic daily load patterns...")
        services = rdg.generate_microservice_dataset(num_services, input_file)
        print(f"Data generated and saved to file '{input_file}'")
    else:
        # Load existing data
        print(f"Loading data from file '{input_file}'...")
        try:
            with open(input_file, 'r') as f:
                services = json.load(f)
            print(f"Loaded {len(services)} microservices")
        except Exception as e:
            print(f"Error loading data: {e}")
            print("Generating new data...")
            services = rdg.generate_microservice_dataset(num_services, input_file)
            print(f"Data generated and saved to file '{input_file}'")
    
    # Test the algorithm
    print("\nRunning the stable group formation algorithm...")
    groups, group_services, slot_sums = main.form_multiple_knapsack_groups(services)
    
    # Analyze results
    print("\nGrouping results:")
    print(f"Number of groups created: {len(groups)}")
    
    # Calculate statistics for each group
    group_stats = []
    for i, (group, service_indices, sums) in enumerate(zip(groups, group_services, slot_sums)):
        mean = sum(sums) / len(sums)
        variance = sum((x - mean) ** 2 for x in sums) / len(sums)
        std_dev = variance ** 0.5
        cv = (std_dev / mean) * 100 if mean > 0 else float('inf')
        
        group_stats.append({
            'group_id': i,
            'size': len(service_indices),
            'mean': mean,
            'std_dev': std_dev,
            'cv': cv,
            'services': service_indices
        })
    
    # Sort groups by coefficient of variation
    group_stats.sort(key=lambda x: x['cv'])
    
    # Output statistics
    print("\nGroup statistics (sorted by coefficient of variation):")
    print(f"{'Group ID':<10} {'Size':<10} {'Avg. load':<15} {'Std. dev.':<15} {'Coef. of var.':<15}")
    print("-" * 65)
    
    for stat in group_stats:
        print(f"{stat['group_id']:<10} {stat['size']:<10} {stat['mean']:.2f}{' '*11} {stat['std_dev']:.2f}{' '*11} {stat['cv']:.2f}%")
    
    # Overall statistics
    all_cvs = [stat['cv'] for stat in group_stats]
    avg_cv = sum(all_cvs) / len(all_cvs) if all_cvs else 0
    min_cv = min(all_cvs) if all_cvs else 0
    max_cv = max(all_cvs) if all_cvs else 0
    
    # Analysis of group sizes
    group_sizes = [stat['size'] for stat in group_stats]
    avg_size = sum(group_sizes) / len(group_sizes) if group_sizes else 0
    min_size = min(group_sizes) if group_sizes else 0
    max_size = max(group_sizes) if group_sizes else 0
    
    print("\nOverall statistics:")
    print(f"Number of microservices: {len(services)}")
    print(f"Number of groups: {len(groups)}")
    print(f"Average group size: {avg_size:.2f} microservices")
    print(f"Min. group size: {min_size}, Max. group size: {max_size}")
    print(f"Average coefficient of variation: {avg_cv:.2f}%")
    print(f"Minimum coefficient of variation: {min_cv:.2f}%")
    print(f"Maximum coefficient of variation: {max_cv:.2f}%")
    
    # Number of "ideal" groups (with coefficient of variation < 5%)
    ideal_groups = len([cv for cv in all_cvs if cv < 5])
    print(f"Number of 'ideal' groups (CV < 5%): {ideal_groups} ({ideal_groups/len(groups)*100:.1f}%)")
    
    # Number of "good" groups (with coefficient of variation < 10%)
    good_groups = len([cv for cv in all_cvs if cv < 10])
    print(f"Number of 'good' groups (CV < 10%): {good_groups} ({good_groups/len(groups)*100:.1f}%)")
    
    # Analysis of best and worst groups
    best_group = group_stats[0]
    worst_group = group_stats[-1]
    
    print("\nBest group:")
    print(f"ID: {best_group['group_id']}, Size: {best_group['size']}, CV: {best_group['cv']:.2f}%")
    
    print("\nWorst group:")
    print(f"ID: {worst_group['group_id']}, Size: {worst_group['size']}, CV: {worst_group['cv']:.2f}%")
    
    # Visualize results
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Visualization of group variation coefficients
        plt.figure(figsize=(12, 6))
        plt.bar(range(len(all_cvs)), all_cvs)
        plt.axhline(y=avg_cv, color='r', linestyle='-', label=f'Average: {avg_cv:.2f}%')
        plt.xlabel('Group index')
        plt.ylabel('Coefficient of variation (%)')
        plt.title('Group variation coefficients')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.savefig('testing/group_variation_coefficients.png')
        print("\nGroup variation coefficients chart saved to file 'testing/group_variation_coefficients.png'")
        
        # Visualization of the best group
        best_group_id = best_group['group_id']
        plt.figure(figsize=(12, 6))
        
        # Visualize the load of each microservice in the group
        hours = list(range(24))
        for i, service_idx in enumerate(group_services[best_group_id]):
            plt.plot(hours, services[service_idx], 'o-', alpha=0.7, label=f'Microservice {service_idx}')
        
        # Visualize the total group load
        plt.plot(hours, slot_sums[best_group_id], 'r--', linewidth=2, label='Total load')
        
        plt.xlabel('Hour of day')
        plt.ylabel('Load')
        plt.title(f'Best group (ID: {best_group_id}, CV: {best_group["cv"]:.2f}%)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(range(0, 24, 2))
        plt.legend()
        plt.savefig('testing/best_group_load.png')
        print("Best group load chart saved to file 'testing/best_group_load.png'")
        
        # Visualization of the worst group
        worst_group_id = worst_group['group_id']
        plt.figure(figsize=(12, 6))
        
        # Visualize the load of each microservice in the group
        for i, service_idx in enumerate(group_services[worst_group_id]):
            plt.plot(hours, services[service_idx], 'o-', alpha=0.7, label=f'Microservice {service_idx}')
        
        # Visualize the total group load
        plt.plot(hours, slot_sums[worst_group_id], 'r--', linewidth=2, label='Total load')
        
        plt.xlabel('Hour of day')
        plt.ylabel('Load')
        plt.title(f'Worst group (ID: {worst_group_id}, CV: {worst_group["cv"]:.2f}%)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(range(0, 24, 2))
        plt.legend()
        plt.savefig('testing/worst_group_load.png')
        print("Worst group load chart saved to file 'testing/worst_group_load.png'")
        
    except ImportError:
        print("\nMatplotlib library is required for visualization")
    except Exception as e:
        print(f"\nVisualization error: {e}")
    
    print("\nTesting completed.")
    return groups, group_services, slot_sums

if __name__ == "__main__":
    # Run with existing data (without generating new data)
    test_realistic_workload(generate_new_data=False) 