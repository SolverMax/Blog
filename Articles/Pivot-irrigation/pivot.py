# Pivot irrigation machine design
# www.solvermax.com

import numpy as np
import numpy_financial as npf
import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import os
import random
import matplotlib.pyplot as plt
import threading

# Situation
FIELD_COST = 640000  # Initial cost of purchasing the field
OPERATING_COST = 180000 # $ per annum, real
WIDTH = 914.400  # Field width, metres
LENGTH = 442.570  # Field length, metres
SEGMENT_LENGTH = 20  # Length of a machine segment, metres
LIFE = 15  # Expected life of the machine, years
MACHINE_COST = 36000  # Cost of the machine, including built-in segments, $
SEGMENT_COST = 12000  # Cost of additional segments, $
SEGMENTS_MIN = 3  # Minimum number of segments, including built-in segments
SEGMENTS_MAX = 8  # Maximum number of segments, including built-in segments
NUM_SEGMENTS = 8
SEGMENTS_BUILTIN = 1  # Number of built-in segments
YIELD_GROSS = 1.35  # Gross yield of crop, $ per square metre per year, real, before tax
WACC = 0.10  # Weighted-average cost of capital, per annum, real, before tax
MAINTAIN_PIVOT = 1000  # Cost of maintaining the pivot and built-in segment, $/year real
MAINTAIN_SEGMENT = 500  # Cost of maintaining additional segments, $/segment/year real

# Solver
EMAIL = 'your_address@example.com'  # Email address required by NEOS. **** Replace with your email address ****
ITERATIONS = 3  # Number of model runs
APPLY_SYMMETRY = False  # Apply the symmetry constraint. The MINLP-BB solver works better if this this False
SOLVER = 'minlp'  # NEOS solver to use, e.g., 'minlp' = MINLP-BB solver, 'knitro', 'couenne'
TIMEOUT = 60  # Stop waiting for reply from NEOS, seconds
TOLERANCE = 0.001  # Tolerance for checking feasibility

os.environ['NEOS_EMAIL'] = EMAIL  # Set user email for NEOS

def create_model():  # Create the optimization model
    model = pyo.ConcreteModel()
    model.Machines = pyo.RangeSet(MACHINES)

    model.segment = pyo.Var(model.Machines, within=pyo.Integers, bounds=(SEGMENTS_MIN, SEGMENTS_MAX))  # Number of segments, including built-in
    model.x = pyo.Var(model.Machines, bounds=(SEGMENTS_MIN * SEGMENT_LENGTH, WIDTH - SEGMENTS_MIN * SEGMENT_LENGTH))  # x center of machine
    model.y = pyo.Var(model.Machines, bounds=(SEGMENTS_MIN * SEGMENT_LENGTH, LENGTH - SEGMENTS_MIN * SEGMENT_LENGTH))  # y center of machine
    
    npv_factor = npf.npv(WACC, [1] * LIFE) / (1 + WACC)  # Cashflows are end-of-year, so defer by (1 + WACC)
    
    def objective_rule(model):  # NPV of pivot irrigator investment
        yield_npv = sum(np.pi * (model.segment[m] * SEGMENT_LENGTH)**2 for m in model.Machines) * npv_factor * YIELD_GROSS
        cost_machines = MACHINES * MACHINE_COST
        cost_segments = sum((model.segment[m] - SEGMENTS_BUILTIN) * SEGMENT_COST for m in model.Machines)
        maintain = (MACHINES*MAINTAIN_PIVOT + sum(model.segment[m] - SEGMENTS_BUILTIN for m in model.Machines)*MAINTAIN_SEGMENT) * npv_factor
        operating_npv = OPERATING_COST * npv_factor
        field_cost = FIELD_COST
        return -(yield_npv - cost_machines - cost_segments - maintain - operating_npv - field_cost)
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
    
    def x_lb_rule(model, m):  # Irrigation circles within west end of field
        return model.x[m] >= model.segment[m] * SEGMENT_LENGTH
    model.x_lb = pyo.Constraint(model.Machines, rule=x_lb_rule)
    
    def x_ub_rule(model, m):  # Irrigation circles within east end of field
        return model.x[m] <= WIDTH - model.segment[m] * SEGMENT_LENGTH
    model.x_ub = pyo.Constraint(model.Machines, rule=x_ub_rule)
    
    def y_lb_rule(model, m):  # Irrigation circles within south end of field
        return model.y[m] >= model.segment[m] * SEGMENT_LENGTH
    model.y_lb = pyo.Constraint(model.Machines, rule=y_lb_rule)
    
    def y_ub_rule(model, m):  # Irrigation circles within north end of field
        return model.y[m] <= LENGTH - model.segment[m] * SEGMENT_LENGTH
    model.y_ub = pyo.Constraint(model.Machines, rule=y_ub_rule)
    
    def no_overlap_rule(model, m, n):  # Irrigation circles must not overlap
        if m > n:
            return (model.x[m] - model.x[n])**2 + (model.y[m] - model.y[n])**2 >= (model.segment[m] * SEGMENT_LENGTH + model.segment[n] * SEGMENT_LENGTH)**2
        return pyo.Constraint.Skip
    model.no_overlap = pyo.Constraint(model.Machines, model.Machines, rule=no_overlap_rule)
    
    if APPLY_SYMMETRY:
        def symmetry_rule(model, m):  # Order the machine sizes, to reduce model symmetry
            if m < MACHINES:
                return model.segment[m] >= model.segment[m + 1]
            return pyo.Constraint.Skip
        model.symmetry = pyo.Constraint(model.Machines, rule=symmetry_rule)

    return model

def initialize_model():  # Create the model object and populate with random initial values
    model = create_model()
    for j in model.Machines:
        model.segment[j].value = random.randint(SEGMENTS_MIN, SEGMENTS_MAX)
        model.x[j].value = random.uniform(SEGMENTS_MIN * SEGMENT_LENGTH, WIDTH - SEGMENTS_MIN * SEGMENT_LENGTH)
        model.y[j].value = random.uniform(SEGMENTS_MIN * SEGMENT_LENGTH, LENGTH - SEGMENTS_MIN * SEGMENT_LENGTH)
    return model

def handle_solver_timeout(solver_thread, iteration):  # Call to NEOS failed to respond within the timeout
    if solver_thread.is_alive():
        print(f'Iteration {iteration+1:>3}, Solver timeout')
        alive = True
    else:
        alive = False
    return alive

def check_solution(model, result):  # Check if we obtained a valid solution
    write_solution = False
    optimal = False
    limit_stop = False
    feasible = False
    condition = result.solver.termination_condition

    if condition == pyo.TerminationCondition.optimal:
        optimal = True
    if condition in (pyo.TerminationCondition.maxTimeLimit, pyo.TerminationCondition.maxIterations):
        limit_stop = True
    if optimal or limit_stop:
        try:
            result.solver.status = pyo.SolverStatus.ok  # Suppress warning about aborted status, if stopped at time limit
            model.solutions.load_from(result)  # Defer loading result until now, in case there is no solution to load
            write_solution = True
        except:
            write_solution = False

    for constraint in model.component_objects(pyo.Constraint, active=True):  # Check that each constraint is feasible, within a tolerance
        for index in constraint:
            if constraint[index].has_lb():
                if pyo.value(constraint[index].lower) is not None:
                    if pyo.value(constraint[index].body) + TOLERANCE >= pyo.value(constraint[index].lower):
                        feasible = True
                        break
            if constraint[index].has_ub():
                if pyo.value(constraint[index].upper) is not None:
                    if pyo.value(constraint[index].body) - TOLERANCE <= pyo.value(constraint[index].upper):
                        feasible = True
                        break
    if not feasible:
        write_solution = False
    
    return write_solution
    
def process_result(result_container, model, best_z, best_solution, iteration):  # Print progress
    if result_container:
        found = True
        result = result_container[0]
        write_solution = check_solution(model, result)
        if write_solution:
            curr_obj = -pyo.value(model.obj)  # Note negation, to convert back to maximization
            obj = max(curr_obj, best_z)
            print(f'Iteration {iteration+1:>3}, objective: {curr_obj:>11,.0f}, best so far: {obj:>11,.0f}')
            if curr_obj > best_z:
                best_z = curr_obj
                best_solution = {j: (pyo.value(model.x[j]), pyo.value(model.y[j]), pyo.value(model.segment[j]) * SEGMENT_LENGTH) for j in model.Machines}
        else:
            print(f'Iteration {iteration+1:>3}, Invalid solution')
    else:
        found = False
        print(f'Iteration {iteration+1:>3}, No solution found')
    return best_z, best_solution, found

def solve_model(model, result_container, opt):  # Call the solver
    model.write('model.gams', io_options={'symbolic_solver_labels': False})
    r = opt.solve(model, load_solutions=False, tee=False, solver=SOLVER, options={})
    result_container.append(r)

def solve_iteration(iteration, opt, best_z, best_solution):  # Solve current iteration, allowing for a timeout interruption
    model = initialize_model()
    result_container = []
    solver_thread = threading.Thread(target=solve_model, args=(model, result_container, opt))
    solver_thread.start()
    solver_thread.join(timeout=TIMEOUT)

    if handle_solver_timeout(solver_thread, iteration):
        found = False
    else:
        best_z, best_solution, found = process_result(result_container, model, best_z, best_solution, iteration)
    return model, best_z, best_solution, found

def run_iterations(iterations):  # Run each iteration of the model, noting the bext solution found (if any)
    best_solution = None
    best_z = -np.inf

    for iteration in range(iterations):
        opt = pyo.SolverManagerFactory('neos')  # Must create a new solver each iteration, to ensure thread safety
        model, best_z, best_solution, found_solution = solve_iteration(iteration, opt, best_z, best_solution)
    print_results(model, found_solution, best_z, best_solution)    

def show_solution(best_solution):  # Show the field with the irrigator machine solution
    for s in best_solution:
        x = best_solution[s][0]
        y = best_solution[s][1]
        r = best_solution[s][2]
        n = best_solution[s][2] / SEGMENT_LENGTH
        print(f'Machine {s:>2}: x = {x:>8,.3f}, y = {y:>8,.3f}, r = {r:>8,.3f}, segments = {n:>3,.0f}')
    
    fig, ax = plt.subplots(figsize=(9, 6))  # Small: 3.6, 2.4; Large: 9, 6
    for s in best_solution:
        x, y, r = best_solution[s]
        circle = plt.Circle((x, y), r, color='green', fill=True, linewidth=0.5)
        ax.add_artist(circle)
        ax.text(x, y, f'{r/SEGMENT_LENGTH:.0f}', color='white', fontsize=10, ha='center', va='center')
    ax.set_xlim((0, WIDTH))
    ax.set_ylim((0, LENGTH))
    ax.set_aspect('equal', adjustable='box')
    ax.set_facecolor('tan')  # Set plot area background
    ax.set_xticks([])  # Remove axis labels and tick marks
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.show()
    print()

def calculate_coverage(best_solution):
    total_area = WIDTH * LENGTH
    covered_area = sum(np.pi * (radius ** 2) for _, _, radius in best_solution.values())
    coverage_percentage = (covered_area / total_area) * 100
    return coverage_percentage

def calc_segments(best_solution):
    num_segments = int(round(sum(radius / SEGMENT_LENGTH for _, _, radius in best_solution.values()), 0))
    return num_segments
    
def print_results(model, found_solution, best_z, best_solution):  # Print best solution (if any)
    print()
    print('Best solution found')
    print('-------------------')
    if best_solution is not None:
        print(f'\nObjective: {best_z:,.0f}')
        cover = calculate_coverage(best_solution)
        print(f'Coverage:  {cover:.2f}%')
        segments = calc_segments(best_solution)
        print(f'Segments:  {segments} (including built-in)\n')
        show_solution(best_solution)
    else:
        print('No solution')

def main():
    print('\nPivot irrigation model')
    print('======================\n')
    print(f'Machines: {MACHINES}\n')
    run_iterations(ITERATIONS)

if __name__ == '__main__':
    for MACHINES in [NUM_SEGMENTS]:  # Number of machines to use
        main()