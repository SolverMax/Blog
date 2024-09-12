# Model 5b, Cable length management, Pyomo MILP parallel

# Import dependencies
import pyomo.environ as pyo
import time as tm
import random as rd
import multiprocessing as mp

# Data
from data.data_08 import *   # Data file, in Python format, like data_08.py
cable_struct = [sorted(row[:2]) + [row[2]] for row in cable_struct]   # Sort the devices in ascending order

# File assumptions
LOG_FILENAME = 'highslog.txt'   # Log file for HiGHS solver
WRITE_MODEL_FILE = False   # Write Pyomo model file

# Run parameters
MODEL_NAME = 'Model 5b: Cable length management, Pyomo MILP parallel'
TIME_LIMIT = 60   # Seconds
NUM_THREADS = 16   # Number of threads to use

# Solver options
SOLVER_NAME = 'appsi_highs'   # Local solver to use
VERBOSE = False   # Turn off verbose solver output
LOAD_SOLUTION = False   # Defer loading a solution until we know if there is a solution to load
PRESOLVE = 'on'   # Perform presolve step, or not
WRITE_LOG_FILE = True   # Write HiGHS log file

def set_up_solver(model, thread_id):   # Create the local Solver object, assumed to be HiGHS
    solver = pyo.SolverFactory(pyo.value(model.Engine))   # Local solver assumed to be installed
    solver.options['time_limit'] = pyo.value(model.TimeLimit)
    solver.options['log_to_console'] = VERBOSE
    if WRITE_LOG_FILE:
        solver.options['log_file'] = f'highslog_{thread_id:02}.txt'   # Sometimes HiGHS doesn't update the console as it solves, so write log file too
    solver.options['presolve'] = PRESOLVE
    solver.options['random_seed'] = rd.randrange(2**31) - 1   # Different seed for each thread
    return solver, model

def call_solver(solver, model):   # Call the local solver
    results = solver.solve(model, load_solutions=LOAD_SOLUTION, tee=VERBOSE)
    return results, model

def get_data():   # Get data from data file
    num_connections = len(cable_struct)   # Number of connections between devices. Each connection may have more than one cable
    num_devices = 0   # Number of devices in the rack
    max_cables = 0   # Maximum cables between any two devices
    length_lb = 0   # Total cable length if all cables are of length 1
    for device_from, device_to, cables in cable_struct:
        num_devices = max(num_devices, device_from, device_to)
        max_cables = max(max_cables, cables)
        length_lb += cables
    num_devices += 1
    max_diff = max_cables * (num_devices - 1)  # Maximum distance between devices * maximum number of cables
    return num_connections, num_devices, max_diff, length_lb
    
def define_model_data(model, num_connections, num_devices, max_diff, length_lb):   # Define model data, assigning all data to the Model
    model.Position = pyo.Set(initialize=range(num_devices))   # Position of device in rack
    model.Cables = pyo.Param(model.Position, model.Position, within=pyo.NonNegativeIntegers, initialize=0, mutable=True)   # Number of cables between devices
    model.NumConnections = num_connections
    model.NumDevices = num_devices
    model.MaxDiff = max_diff
    model.LengthLB = length_lb
    
    for device_from, device_to, cables in cable_struct:
        model.Cables[device_from, device_to] = cables
    
    return model

def define_model(model):   # Define the model as a Mixed Integer Linear Program
    model.Allocation = pyo.Var(model.Position, within=pyo.NonNegativeIntegers, bounds=(0, model.NumDevices - 1), initialize=0)   # Position of device in rack
    model.AllDiff = pyo.Var(model.Position, model.Position, within=pyo.Binary, initialize=0)   # Make each rack position unique
    model.AbsLength = pyo.Var(model.Position, model.Position, within=pyo.NonNegativeIntegers, bounds=(0, model.NumDevices - 1), initialize=0)   # Absolute value of cable length
    model.d1 = pyo.Var(model.Position, model.Position, within=pyo.Binary, initialize=0)   # Helper for calculation of absolute value
    model.d2 = pyo.Var(model.Position, model.Position, within=pyo.Binary, initialize=0)   # Helper for calculation of absolute value
    
    def rule_position_allocation(model, p):   # Allocate each device to a unique position in the rack
        return model.Allocation[p] == sum(q * model.AllDiff[p, q] for q in model.Position)
    model.PositionAllocation = pyo.Constraint(model.Position, rule=rule_position_allocation)
    
    def rule_diff1(model, p):   # All Different constraint, part 1
        return sum(model.AllDiff[p, q] for q in model.Position) == 1
    model.Diff1 = pyo.Constraint(model.Position, rule=rule_diff1)

    def rule_diff2(model, q):   # All Different constraint, part 2
        return sum(model.AllDiff[p, q] for p in model.Position) == 1
    model.Diff2 = pyo.Constraint(model.Position, rule=rule_diff2)
    
    def rule_lb1(model, p, q):   # Absolute value constraint, part 1
        if p < q:
            return model.AbsLength[p, q] - (model.Allocation[p] - model.Allocation[q]) >= 0
        else:
            return pyo.Constraint.Skip
    model.LB1 = pyo.Constraint(model.Position, model.Position, rule=rule_lb1)

    def rule_lb2(model, p, q):   # Absolute value constraint, part 2
        if p < q:
            return model.AbsLength[p, q] - (model.Allocation[q] - model.Allocation[p]) >= 0
        else:
            return pyo.Constraint.Skip
    model.LB2 = pyo.Constraint(model.Position, model.Position, rule=rule_lb2)
    
    def rule_ub1(model, p, q):   # Absolute value constraint, part 3
        if p < q:
            return model.AbsLength[p, q] - (model.Allocation[p] - model.Allocation[q]) <= 2 * (model.NumDevices - 1) * model.d2[p, q]
        else:
            return pyo.Constraint.Skip
    model.UB1 = pyo.Constraint(model.Position, model.Position, rule=rule_ub1)

    def rule_ub2(model, p, q):   # Absolute value constraint, part 4
        if p < q:
            return model.AbsLength[p, q] - (model.Allocation[q] - model.Allocation[p]) <= 2 * (model.NumDevices - 1) * model.d1[p, q]
        else:
            return pyo.Constraint.Skip
    model.UB2 = pyo.Constraint(model.Position, model.Position, rule=rule_ub2)

    def rule_d1d2(model, p, q):   # Absolute value constraint, part 5
        if p < q:
            return model.d1[p, q] + model.d2[p, q] == 1
        else:
            return pyo.Constraint.Skip
    model.d1d2 = pyo.Constraint(model.Position, model.Position, rule=rule_d1d2)

    def rule_extra(model):   # Additional constraint, lower bound if all lengths are 1
        return sum(model.Cables[p, q] * model.AbsLength[p, q] for p in model.Position for q in model.Position) >= model.LengthLB
    model.Extra = pyo.Constraint(rule=rule_extra)

    for p in model.Position:
        for q in model.Position:
            if p >= q:
                model.AbsLength[p, q].fix(0)
                model.d1[p, q].fix(0)
                model.d1[p, q].fix(0)

    def rule_obj(model):   # Min total length of cables
        return sum(model.Cables[p, q] * model.AbsLength[p, q] for p in model.Position for q in model.Position)
    model.Obj = pyo.Objective(rule=rule_obj, sense=pyo.minimize)

    return model

def check_solution(model, results):   # Check if we obtained a valid solution
    write_solution = False
    optimal = False
    limit_stop = False
    condition = results[0].solver.termination_condition

    if condition == pyo.TerminationCondition.optimal:
        optimal = True
    if condition in (pyo.TerminationCondition.maxTimeLimit, pyo.TerminationCondition.maxIterations):
        limit_stop = True
    if optimal or limit_stop:
        try:
            results[0].solver.status = pyo.SolverStatus.ok   # Suppress warning about aborted status, if stopped at time limit
            write_solution = True
            model.solutions.load_from(results[0])   # Defer loading results until now, in case there is no solution to load
        except:
            write_solution = False
    
    return write_solution, condition

def write_thread_solution(model, write_solution, thread_id, condition, elapsed_time):   # Write solution for a thread
    if write_solution:
        objective_value = pyo.value(model.Obj)
        best_case = [round(pyo.value(model.Allocation[u]), 0) for u in range(len(model.Allocation))]
        print(f"\nThread {thread_id} completed in {elapsed_time:.2f} seconds:")
        print(f"Status: {condition}")
        print(f"Objective: {objective_value:,.0f}")
        print("Position     Device")
        for v, pos in enumerate(best_case):
            curr_name = chr(best_case.index(v) + ord("A"))
            print(f'{v + 1:>8}    {curr_name:>7}')   # Assumes devices are named A, B, C, etc
        print('-' * 40)
    else:
        print(f"\nThread {thread_id} completed in {elapsed_time:.2f} seconds:")
        print(f"Status: {condition}")
        print("No feasible solution found.")
        print('-' * 40)

    return objective_value, best_case

def run_model_thread(lock, thread_id):   # Create and run a single thread
    start_time = tm.time()
    model = pyo.ConcreteModel(name=f"{MODEL_NAME} - Thread {thread_id}")
    num_connections, num_devices, max_diff, length_lb = get_data()
    model.Engine = SOLVER_NAME
    model.TimeLimit = TIME_LIMIT
    solver, model = set_up_solver(model, thread_id)
    model = define_model_data(model, num_connections, num_devices, max_diff, length_lb)
    model = define_model(model)
    if WRITE_MODEL_FILE:
        model.write(f'Model_thread_{thread_id}.gams', io_options={'symbolic_solver_labels': False})
    results = call_solver(solver, model)
    write_solution, condition = check_solution(model, results)
    end_time = tm.time()
    elapsed_time = end_time - start_time
    with lock:   # Acquire thread lock so that different threads don't print simultaneously
        objective_value, best_case = write_thread_solution(model, write_solution, thread_id, condition, elapsed_time)
    return thread_id, condition, objective_value, best_case, elapsed_time

def write_summary(all_results):   # Write summary of all threads
    print("\nSummary of all threads:\n")
    print(f"{'Thread':<10} {'Status':<15} {'Seconds':<10} {'Objective':<20}")
    print('-' * 47)
    for thread_id, condition, objective_value, best_case, elapsed_time in all_results:
        if objective_value is not None:
            objective_str = f"{objective_value:,.0f}"
        else:
            objective_str = "x"
        print(f"{thread_id:>4}       {condition:<15} {elapsed_time:<10.1f} {objective_str:>9}")
    print('-' * 47)
    
def main(threads):   # Run the model
    print(MODEL_NAME, '\n')
    with mp.Manager() as manager:   # Create manager to pass lock to threads; necessary on Windows
        lock = manager.Lock()
        with mp.Pool(processes=mp.cpu_count()) as pool:
            results = [pool.apply_async(run_model_thread, (lock, i,)) for i in range(threads)]
            all_results = [result.get() for result in results]
        all_results.sort(key=lambda x: x[0])  # Sort results by thread_id
        write_summary(all_results)

if __name__ == '__main__':
    main(NUM_THREADS)