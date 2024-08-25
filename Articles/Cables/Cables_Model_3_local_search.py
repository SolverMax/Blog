# Cabling management, Model 3: Local search
# We search for solutions by starting with a random sample of rack positions for the devices, then randomly swap two device positions. We retain the new solution if it is better. To provide variety, a new random order has a probability of being created at a specified interval. The search continues for the specified time.
# The search is run in parallel on each cpu core/thread.

import time
import math
import random
import multiprocessing as mp
import copy

# Data
from data.data_08 import cable_struct   # Data file in the data folder, in Python format, like data.data_08.py

# Constants
MAX_TIME = 60   # Maximum overall run time, seconds
MAX_TIME_BUFFER = 1   # Small buffer to allow final iteration of results to print, seconds
UPDATE_INTERVAL = 5   # Time interval for printing current best solution, seconds
RESTART_INTERVAL = 10   # Time interval for restarting each process, seconds
RESTART_PROBABILITY = 0.5  # Probability of a thread restarting with a random order at each restart interval

def index_to_letter(index):   # Convert number to character, 'A' is 65 in ASCII, 'a' is 97
    return chr(ord('A') + index) if index < 26 else chr(ord('a') - 26 + index)
    
def calculate_num_devices(cable_structure):   # Number of devices in input data
    return max(max(device_from, device_to) for device_from, device_to, _ in cable_structure) + 1

def calculate_total_length(order, cable_structure):   # Total cable length of current solution
    return sum(abs((order[device_from] - order[device_to]) * cables) for device_from, device_to, cables in cable_structure)

def print_progress(elapsed_time, min_length, pct_done, new_best):   # Print current solution, marking with asterisk if best found so far
    print(f'{elapsed_time:>9,.0f}  {pct_done:>7,.2%}   {min_length:>4,.0f}', f'*' if new_best else f'')

def print_header():    # Header for progress updates
    print('Model 2: Cable length management, local search in parallel\n')
    print('     Time    %done     Best')
    print('---------------------------')
    
def local_search_chunk(cable_struct, num_devices, start_time, shared_dict, max_time):   # Each processor's chunk of the search
    local_min_length = float('inf')   # Best length found by this process
    local_best_case = []   # Best case found by this process
    order = list(range(num_devices))
    random.shuffle(order)
    min_length = calculate_total_length(order, cable_struct)
    last_update = time.time()
    last_restart = time.time()
    local_count = 0
    
    while time.time() - start_time < max_time + MAX_TIME_BUFFER:
        new_order = copy.deepcopy(order[:])
        i, j = random.sample(range(num_devices), 2)
        new_order[i], new_order[j] = new_order[j], new_order[i]
        new_length = calculate_total_length(new_order, cable_struct)
        if new_length < min_length:
            order = copy.deepcopy(new_order)
            local_best_case = copy.deepcopy(new_order)
            min_length = new_length

        local_count += 1
        current_time = time.time()
        if current_time - last_update >= UPDATE_INTERVAL:   # At some interval, co-ordinate with other processes to note progress. Multiple processes may print an update
            with shared_dict['lock']:
                elapsed_time = current_time - start_time
                pct_done = elapsed_time / max_time
                if min_length < shared_dict['min_length']:   # Update best solution found so far (note <)
                    shared_dict['new_best'] = True
                    shared_dict['min_length'] = min_length
                    shared_dict['best_case'] = local_best_case
                    shared_dict['pct_done'] = pct_done
                if (min_length <= shared_dict['min_length']) and (pct_done >= shared_dict['last_pct_done']):   # Print progress, even if no improvement (note <=)
                    shared_dict['last_pct_done'] = pct_done
                    print_progress(elapsed_time, min_length, pct_done, shared_dict['new_best'])
                    shared_dict['new_best'] = False
                shared_dict['total_count'] += local_count
                local_count = 0
            last_update += UPDATE_INTERVAL   # Defer updating until next regular update time
        
        current_time = time.time()
        if current_time - last_restart >= RESTART_INTERVAL:   # Potentially restart with a new random order every RESTART_INTERVAL seconds
            if random.random() <= RESTART_PROBABILITY:
                random.shuffle(order)
            else:
                order = copy.deepcopy(shared_dict['best_case'])
            last_restart = current_time
        
        if (current_time - start_time) >= max_time + MAX_TIME_BUFFER:   # Stop search if reached maximum overall run time
            break
    return min_length, order

def run_pool(num_devices, num_processes, cable_struct, start_time):   # Establish and run the processor pool
    with mp.Manager() as manager:
        shared_dict = manager.dict()   # Data structure shared by the processors, to capture current best state
        shared_dict['min_length'] = float('inf')
        shared_dict['best_case'] = list(range(num_devices))
        shared_dict['pct_done'] = 0
        shared_dict['last_pct_done'] = 0
        shared_dict['new_best'] = False
        shared_dict['total_count'] = 0
        shared_dict['lock'] = manager.Lock()

        pool = mp.Pool(processes = num_processes)
        results = [pool.apply_async(local_search_chunk, (cable_struct, num_devices, start_time, shared_dict, MAX_TIME))
                                    for _ in range(num_processes)]
        results = [res.get() for res in results]   # Collate results from each process
        order_count = shared_dict['total_count']   # Retrieve the total order count before it is lost when the threads end
    return results, order_count
    
def print_results(results, num_devices, total_count, start_time):   # Print final results after processor pool completes
    min_length = min(res[0] for res in results)
    best_case = next(res[1] for res in results if res[0] == min_length)
    run_time = time.time() - start_time
    print(f'\nDevices: {num_devices}')
    print(f'Minimum length: {min_length}')
    print(f'Best case: {[index_to_letter(best_case.index(v)) for v in range(len(best_case))]}')   # 0 is at index 4 of [5, 4, 7, 1, 0, 3, 2, 6], so index 0 of result is 'A' + 4 -> 'E', etc
    print(f'Rate: {total_count/run_time:,.0f} orders per second')
    print(f'Time: {run_time:,.2f} seconds')

def main():
    start_time = time.time()
    num_devices = calculate_num_devices(cable_struct)
    num_processes = mp.cpu_count()
    print_header()
    results, total_count = run_pool(num_devices, num_processes, cable_struct, start_time)
    print_results(results, num_devices, total_count, start_time)

if __name__ == "__main__":
    main()
