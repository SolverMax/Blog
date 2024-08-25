# Model 4, Cable length management, OR-Tools

# Imports
from ortools.sat.python import cp_model
import pandas as pd
import time as time
from threading import Timer

# Data
from data.data_12 import *   # Data file, in Python format, like data_08.py

# Globals
MODEL_NAME = 'Model 4: Cable length management, OR-Tools constraint programming'
MAX_TIME = 30   # seconds. Maximum time for each phase separately
MAX_NO_IMPROVEMENT = 3600   # seconds. Stop if no improvement; only for Phase 1
WORKERS = 24   # Number of parallel workers to use in Phase 1 (Phase 2 is always single-threaded). **** Change to match the number of threads on your PC
SEARCH_ALL = False   # Search for all solutions with objective function value found in Phase 1

# Data
def get_data():
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

# Printing
def print_heading(MODEL_NAME):
    print(f"{MODEL_NAME}\n")
    print('Intermediate solutions')
    print('======================================\n')
    print('Solution    Seconds    Length    Bound')
    print('--------------------------------------')
    
class IntermediateSolutionPrinter(cp_model.CpSolverSolutionCallback):   # Print intermediate solutions and stop if no improvement for n seconds
    def __init__(self, variables):
        cp_model.CpSolverSolutionCallback.__init__(self)
        super().__init__()
        self.__variables = variables
        self.__solution_count = 0
        self.__start_time: float = time.time()
       
        self._timer_limit = MAX_NO_IMPROVEMENT   # 'Stop if no improvement' code based on https://groups.google.com/g/or-tools-discuss/c/XuY3dozvVMI/m/GOLS_IrwAgAJ
        self._timer = None

    def on_solution_callback(self):
        current_time = time.time()
        obj = self.ObjectiveValue()
        print(f'{self.__solution_count:>8,.0f}   {current_time - self.__start_time:>8,.2f} {obj:>9,.0f}  {self.BestObjectiveBound():>7,.0f}')
        self.__solution_count += 1
        self._reset_timer()

    def solution_count(self):
        return self.__solution_count

    def _reset_timer(self):
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(self._timer_limit, self.stop_search)
        self._timer.start()

    def stop_search(self):
        if phase_1:   # Interrupt applies only to Phase 1
            print(f'\n{self._timer_limit} seconds without improvement')
            super().stop_search()
        else:
            if self._timer:   # Cancel the open timer, if there is one
                self._timer.cancel()
        
def print_solution(status, solver, model, position, length, connection_list, device_list):   # Print solution, if there is one, after solve
    print('\nSolution')
    print('======================================\n')
    print(f'Status:   ', solver.StatusName(status))
    print(f'Objective: {solver.ObjectiveValue():<7,.0f}')
    print(f'Run time:  {solver.WallTime():,.2f} seconds\n')
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print('Position     Device')
        for i in device_list:
            for m in device_list:
                if solver.Value(position[m]) == i:
                    curr_name = chr(m + ord('A'))   # Assumes devices are named A, B, C, etc
                    print(f'{solver.Value(position[m]) + 1:>8}    {curr_name:>7}')
        print('\nConnection    Length')
        for c in connection_list:
            print(f'{c + 1:>10}    {solver.Value(length[c]):>6}')
        print('--------------------')
        print(f'Total {solver.ObjectiveValue():>14.0f}')

# Printer for all solutions
class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):

    def __init__(self, variables):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.__solution_count = 0
            
    def on_solution_callback(self):
        self.__solution_count += 1
        print('Position     Device')
        for i in range(len(self.__variables[0])):
            for m in range(len(self.__variables[0])):
                v = self.Value(self.__variables[0][m])
                if v == i:
                    curr_name = chr(m + ord('A'))   # Assumes devices are named A, B, C, etc
                    print(f'{v + 1:>8}    {curr_name:>7}')        
        print()

    def solution_count(self):
        return self.__solution_count

# Formulation
def formulation(cable_struct, num_connections, num_devices, max_diff, phase_1, best, length_lb):
    model = cp_model.CpModel()

    connection_list = pd.RangeIndex(num_connections)
    device_list = pd.RangeIndex(num_devices)
    position = model.NewIntVarSeries(index = device_list, lower_bounds = 0, upper_bounds = num_devices - 1, name = "Position")
    length = model.NewIntVarSeries(index = connection_list, lower_bounds = 0, upper_bounds = max_diff, name = "Length")
    
    model.AddAllDifferent(position)   # The devices must occupy different positions in the rack

    for i, (device_from, device_to, cables) in enumerate(cable_struct):    # Cable length between devices
        model.AddAbsEquality(length[i], (position[device_from] - position[device_to]) * cables)   # Note the absolute value used for calculating length

    model.Add(sum(length) >= length_lb)   # Additional constraint, lower bound if all lengths are 1
    
    if phase_1:
        model.Minimize(sum(length))   # In Phase 1, minimize the total cable length
    else:
        model.Add(sum(length) == best)   # For subsequent runs, find solutions with cable length found in Phase 1

    return model, position, length, connection_list, device_list

# Find minimum cable length
def find_min_length(MODEL_NAME, phase_1, best):
    num_connections, num_devices, max_diff, length_lb = get_data()
    model, position, length, connection_list, device_list = formulation(cable_struct, num_connections, num_devices, max_diff, phase_1, best, length_lb)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = MAX_TIME
    solver.parameters.num_workers = WORKERS
    solution_printer = IntermediateSolutionPrinter([position, length])
    print_heading(MODEL_NAME)
    status = solver.Solve(model, solution_printer)
    print_solution(status, solver, model, position, length, connection_list, device_list)
    best = solver.ObjectiveValue()
    return best

# Search for all solutions
def search_for_all(best):   # Search for all solutions with objective equal to solution found above
    num_connections, num_devices, max_diff, length_lb = get_data()
    model, position, length, connection_list, device_list = formulation(cable_struct, num_connections, num_devices, max_diff, phase_1, best, length_lb)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = MAX_TIME

    print('\nAll solutions')
    print('===================\n')
    
    solution_printer_all = VarArraySolutionPrinter([position, length])
    status = solver.SearchForAllSolutions(model, solution_printer_all)

    print('Status = %s' % solver.StatusName(status))
    print('Number of solutions found: %i' % solution_printer_all.solution_count())
    print(f'Run time:  {solver.WallTime():,.2f} seconds\n')

# Phase 1: Find the minimum cable length
phase_1 = True
best = None
best = find_min_length(MODEL_NAME, phase_1, best)
phase_1 = False

# Phase 2. Find all solutions with the minimum cable length found in Phase 1
if SEARCH_ALL:
    best = int(best)
    search_for_all(best)