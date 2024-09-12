# Model 5a, Cable length management, Pyomo MILP

# Import dependencies
import pyomo.environ as pyo

# Data
from data.data_08 import *   # Data file, in Python format, like data_08.py
cable_struct = [sorted(row[:2]) + [row[2]] for row in cable_struct]   # Sort the devices in ascending order

# File assumptions
LOG_FILENAME = 'highslog.txt'   # Log file for HiGHS solver
MODEL_FILENAME = 'Model5a.gams'  # Name of model file
WRITE_MODEL_FILE = True   # Write Pyomo model file

# Run parameters
MODEL_NAME = 'Model 5a: Cable length management, Pyomo MILP'
TIME_LIMIT = 30   # Seconds

# Solver options
SOLVER_NAME = 'appsi_highs'   # Local solver to use
VERBOSE = False   # Turn off verbose solver output
LOAD_SOLUTION = False   # Defer loading a solution until we know if there is a solution to load
PRESOLVE = 'on'   # Perform presolve step, or not
WRITE_LOG_FILE = False   # Write HiGHS log file

def set_up_solver(model):   # Create the local Solver object, assumed to be HiGHS
    solver = pyo.SolverFactory(pyo.value(model.Engine))   # Local solver assumed to be installed
    solver.options['time_limit'] = pyo.value(model.TimeLimit)
    solver.options['log_to_console'] = VERBOSE
    if WRITE_LOG_FILE:
        solver.options['log_file'] = LOG_FILENAME   # Sometimes HiGHS doesn't update the console as it solves, so write log file too
    solver.options['presolve'] = PRESOLVE
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

def write_output(model, write_solution, condition):   # Write the solution and related information
    if write_solution:
        print(f'Status:    {condition}')
        print(f'Objective: {pyo.value(model.Obj):,.0f}')
        print('\nPosition     Device')
        best_case = [round(pyo.value(model.Allocation[u]), 0) for u in range(len(model.Allocation))]
        for v in range(len(model.Allocation)):
            index = best_case.index(v)
            curr_name = chr(index + ord("A"))
            print(f'{v + 1:>8}    {curr_name:>7}')   # Assumes devices are named A, B, C, etc
    else:
        exit_message = 'No feasible solution found. Check that the data is valid'
        print(exit_message)
        raise SystemExit(0)

def main():   # Run the model
    print(MODEL_NAME, '\n')
    model = pyo.ConcreteModel(name=MODEL_NAME)
    num_connections, num_devices, max_diff, length_lb = get_data()
    model.Engine = SOLVER_NAME
    model.TimeLimit = TIME_LIMIT
    solver, model = set_up_solver(model)
    model = define_model_data(model, num_connections, num_devices, max_diff, length_lb)
    model = define_model(model)
    if WRITE_MODEL_FILE:
        model.write(MODEL_FILENAME, io_options={'symbolic_solver_labels': False})
    results = call_solver(solver, model)
    write_solution, condition = check_solution(model, results)
    write_output(model, write_solution, condition)
        
if __name__ == '__main__':
    main()