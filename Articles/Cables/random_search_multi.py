# Cabling management, Model 2: Random sample of cases
# We search for solutions using a random sample of rack positions for the devices. The search continues for the specified time, or the number of samples, whichever occurs first.
# The cases are divided into equal chucks for each cpu core/thread and run in parallel.

import time
import math
import random
import multiprocessing as mp
import copy

# Data
from data.data_12 import cable_struct   # Data file in the data folder, in Python format, like data.data_08.py

# Constants
MAX_TIME = 60   # Maximum overall run time, seconds
UPDATE_INTERVAL = 5   # Time interval for printing current best solution, seconds

def index_to_letter(index):   # Convert number to character, 'A' is 65 in ASCII, 'a' is 97
    return chr(ord('A') + index) if index < 26 else chr(ord('a') - 26 + index)
    
def calculate_num_devices(cable_structure):   # Number of devices in input data
    return max(max(device_from, device_to) for device_from, device_to, _ in cable_structure) + 1

def calculate_total_length(order, cable_structure):   # Total cable length of current solution
    return sum(abs((order[device_from] - order[device_to]) * cables) for device_from, device_to, cables in cable_structure)

def print_progress(elapsed_time, min_length, pct_done, new_best):   # Print current solution, marking with asterisk if best found so far
    print(f'{elapsed_time:>9,.0f}  {pct_done:>7,.2%}   {min_length:>4,.0f}', f'*' if new_best else f'')

def print_header():    # Header for progress updates
    print('Model 2: Cable length management, random sample in parallel\n')
    print('     Time    %done     Best')
    print('---------------------------')
    
def cable_layout_chunk(start, end, cable_struct, num_devices, start_time, shared_dict, max_time):   # Each processor's chunk of the solution space
    local_min_length = float('inf')   # Best length found by this process
    local_best_case = []   # Best case found by this process
    order = list(range(num_devices))
    last_update = time.time()
    
    for done in range(start, end):
        random.shuffle(order)   # Create a random device order
        length = calculate_total_length(order, cable_struct)
        
        if length < local_min_length:
            local_best_case = copy.deepcopy(order)   # Need deep copy as order is shuffled in place 
            local_min_length = length

        current_time = time.time()
        if current_time - last_update >= UPDATE_INTERVAL:   # At some interval, co-ordinate with other processes to note progress. Multiple processes may print an update
            with shared_dict['lock']:
                pct_done = (done - start) / (end - start)
                if local_min_length < shared_dict['min_length']:   # Update best solution found so far (note <)
                    shared_dict['new_best'] = True
                    shared_dict['min_length'] = local_min_length
                    shared_dict['best_case'] = local_best_case
                    shared_dict['pct_done'] = pct_done
                if (local_min_length <= shared_dict['min_length']) and (pct_done >= shared_dict['last_pct_done']):   # Print progress, even if no improvement (note <=)
                    elapsed_time = current_time - start_time
                    shared_dict['last_pct_done'] = pct_done
                    print_progress(elapsed_time, local_min_length, pct_done, shared_dict['new_best'])
                    shared_dict['new_best'] = False
            last_update += UPDATE_INTERVAL   # Defer updating until next regular update time
        
        if (current_time - start_time) >= max_time:   # Stop search if reached maximum overall run time
            break
    return local_min_length, local_best_case, done - start + 1

def run_pool(num_devices, num_processes, chunk_size, num_cases, cable_struct, start_time):   # Establish and run the processor pool
    with mp.Manager() as manager:
        shared_dict = manager.dict()   # Data structure shared by the processors, to capture current best state
        shared_dict['min_length'] = float('inf')
        shared_dict['best_case'] = list(range(num_devices))
        shared_dict['pct_done'] = 0
        shared_dict['last_pct_done'] = 0
        shared_dict['new_best'] = False
        shared_dict['lock'] = manager.Lock()

        pool = mp.Pool(processes = num_processes)
        results = [pool.apply_async(cable_layout_chunk, (i * chunk_size,
                                                        ((i + 1) * chunk_size if i < num_processes - 1 else num_cases),
                                                        cable_struct, num_devices, start_time, shared_dict, MAX_TIME))
                                                        for i in range(num_processes)]
        results = [res.get() for res in results]   # Collate results from each process
    return results
    
def print_results(results, num_devices, num_cases, start_time):   # Print final results after processor pool completes
    min_length = min(res[0] for res in results)
    best_case = next(res[1] for res in results if res[0] == min_length)
    done = sum(res[2] for res in results)
    run_time = time.time() - start_time
    print(f'\nDevices: {num_devices}')
    print(f'Minimum length: {min_length}')
    print(f'Best case: {[index_to_letter(best_case.index(v)) for v in range(len(best_case))]}')   # 0 is at index 4 of [5, 4, 7, 1, 0, 3, 2, 6], so index 0 of result is 'A' + 4 -> 'E', etc
    print(f'Done {done:,.0f} of {num_cases:,.0f} cases ({done / num_cases:,.2%})')
    print(f'Time: {run_time:,.2f} seconds')
    print(f'Rate: {done / run_time:,.0f} cases per second\n' if run_time else f'Rate: Undefined\n')

def main():
    start_time = time.time()
    num_devices = calculate_num_devices(cable_struct)
    num_cases = math.factorial(num_devices)  # Arbitrary number probably large enough to find a good solution
    num_processes = mp.cpu_count()
    chunk_size = num_cases // num_processes
    print_header()
    results = run_pool(num_devices, num_processes, chunk_size, num_cases, cable_struct, start_time)
    print_results(results, num_devices, num_cases, start_time)

if __name__ == "__main__":
    main()