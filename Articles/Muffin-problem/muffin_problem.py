# The Muffin Problem
# www.solvermax.com

from pyomo.environ import *
from fractions import Fraction
import math as math
from functools import reduce
import multiprocessing as mp
from datetime import datetime

# Run constants
UB_MUFFINS = 9  # Number of muffins
UB_STUDENTS = 9  # Number of students
TIME_LIMIT = 300  # Seconds

# Solver constants
SOLVER_NAME = 'appsi_highs'   # Local solver to use
VERBOSE = False   # Turn off verbose solver output
LOAD_SOLUTION = False   # Defer loading a solution until we know if there is a solution to load
MODEL_NAME = 'Muffin cutting'

# Other constants
FRACTION_LIMIT = 1000  # Keep fractions to smallish values
NUM_PROCESSES = 16  # Number of processes to run in parallel, limited by number of CPUs

# Derived globals
PROCESSES_TO_USE = min(NUM_PROCESSES, mp.cpu_count())

def to_fraction(input_decimal):  # Convert a value to a fraction
    return Fraction(input_decimal).limit_denominator(FRACTION_LIMIT)  # limit_denominator is supposed to make small fractions, but doesn't always work

def proper_fraction(input_fraction):  # Express as a proper faction, e.g. 7/5 becomes 1 2/5
    whole_number = input_fraction.numerator // input_fraction.denominator
    fraction_part = Fraction(input_fraction.numerator % input_fraction.denominator, input_fraction.denominator).limit_denominator(FRACTION_LIMIT)
    if whole_number != 0:
        return f'{whole_number} {fraction_part}' if fraction_part != 0 else f'{whole_number}'
    else:
        return str(fraction_part)
        
def lcd(fractions):  # Compute the least common denominator (LCD) of a list of fractions
    lcd_value = 1
    for f in fractions:
        lcd_value = lcd_value * f.denominator // math.gcd(lcd_value, f.denominator)
    return lcd_value

def show_as_lcd(f, lcd_value):  # Convert a fraction to the given least common denominator (LCD)
    numerator = str(f.numerator * (lcd_value // f.denominator)).rjust(len(str(lcd_value)), ' ')
    return f'{numerator}/{lcd_value}'

def setup_model(num_muffins, num_students):  # Create the optimization model
    model = ConcreteModel(name=MODEL_NAME)
    model.muffins = RangeSet(num_muffins)
    model.students = RangeSet(num_students)
    model.size = Var(model.muffins, model.students, domain=NonNegativeReals, bounds=(0, 1))  # Size of each piece
    model.smallest = Var(domain=NonNegativeReals)  # Size of the smallest piece
    model.delta = Var(model.muffins, model.students, domain=Binary)  # Linking variable

    model.objective = Objective(expr=model.smallest, sense=maximize)

    model.constraints = ConstraintList()
    for s in model.students:
        model.constraints.add(sum(model.size[m, s] for m in model.muffins) == num_muffins / num_students)  # Each student receives an equal share
    for m in model.muffins:
        model.constraints.add(sum(model.size[m, s] for s in model.students) == 1)  # Slicies are of a whole muffin
    for m in model.muffins:
        for s in model.students:
            model.constraints.add(model.size[m, s] <= model.delta[m, s])  # If delta is 0, size must be 0
            model.constraints.add(model.smallest <= model.size[m, s] + (1 - model.delta[m, s]))  # If delta is 1, smallest <= size

    for s in range(1, num_students):
        model.constraints.add(model.size[1, s] <= model.size[1, s + 1])  # Symmetry-breaking for students
    for m in range(1, num_muffins):
        model.constraints.add(model.size[m, 1] <= model.size[m + 1, 1])  # Symmetry-breaking for muffins
        
    model.bounds = ConstraintList()  # Known bounds from the literature
    model.bounds.add(model.smallest >= 1/num_students)
    if not (num_muffins % num_students == 0):
        model.bounds.add(model.smallest <= 0.5)
    if num_muffins > num_students:
        model.bounds.add(model.smallest >= 1/3)

    return model

def solve_model(model):
    solver = SolverFactory('appsi_highs')
    solver.options['time_limit'] = TIME_LIMIT
    solver.options['mip_rel_gap'] = 0
    results = solver.solve(model, load_solutions=LOAD_SOLUTION, tee=VERBOSE)
    return results

def check_solution(model, results):   # Check if we obtained a valid solution
    write_solution = False
    optimal = False
    limit_stop = False
    condition = results.solver.termination_condition

    if condition == TerminationCondition.optimal:
        optimal = True
    if condition in (TerminationCondition.maxTimeLimit, TerminationCondition.maxIterations):
        limit_stop = True
    if optimal or limit_stop:
        try:
            results.solver.status = SolverStatus.ok   # Suppress warning about aborted status, if stopped at time limit
            write_solution = True
            model.solutions.load_from(results)   # Defer loading results until now, in case there is no solution to load
        except:
            write_solution = False
    return write_solution, condition

def calculate_total_muffins(model, num_muffins, num_students, distinct_sizes):
    student_total = Fraction(0)
    for size in distinct_sizes:
        count = sum(1 for m in model.muffins for s in model.students if to_fraction(model.size[m, s]()) == size)
        student_total += size * count
    per_student = student_total / num_students
    return per_student

def display_case_result(case_num, num_muffins, num_students, results, model, lcd_value, per_student, distinct_sizes, condition, time_dict):
    best_bound = results['Problem'][0]['Upper bound']
    current_solution = value(model.smallest)
    gap = abs(best_bound - current_solution) / abs(current_solution) * 100 if current_solution != 0 else float('inf')
    proper = proper_fraction(per_student)
    sizes_list = [f'{sum(1 for s in model.students for m in model.muffins if to_fraction(model.size[m, s]()) == size)}x{to_fraction(size)}' for size in distinct_sizes]
    sizes = ', '.join(sizes_list)
    run_time = (time_dict[case_num, 1] - time_dict[case_num, 0]).total_seconds()
    c = f'{case_num + 1:>4}'
    m = f'{num_muffins:>3}'
    s = f'{num_students:>3}'
    t = f'{run_time:>7.1f}'
    o = f'{current_solution:.6f}'
    f = f'{str(to_fraction(current_solution)):>7}'
    g = f'{gap:>6.2f}%'
    d = f'{condition:>12}'
    p = f'{proper:>8}'
    z = f'{sizes}'
    print(f'{c}        {m}        {s}  {t}     {o}     {f}     {g}    {d}        {p}     {z}')
    return current_solution, gap

def case_result(case_num, num_muffins, num_students, model, results, write_solution, condition, time_dict):
    time_dict[case_num, 1] = datetime.now()
    if write_solution:
        all_fractions = [to_fraction(model.size[m, s]()) for m in model.muffins for s in model.students]
        all_fractions = [f for f in all_fractions if f != Fraction(0, 1)]  # Filter out results like 0/1
        lcd_value = lcd(all_fractions)
        distinct_sizes = sorted(set(all_fractions))
        per_student = calculate_total_muffins(model, num_muffins, num_students, distinct_sizes)
        obj, gap = display_case_result(case_num, num_muffins, num_students, results, model, lcd_value, per_student, distinct_sizes, condition, time_dict)
    else:
        obj = -1
        gap = 0
        print('No feasible solution found.')
    return obj, gap

def setup(args):
    num_muffins, num_students = args
    print(f'{MODEL_NAME} with up to {num_muffins} muffins and {num_students} students')
    print(f'\nCase    Muffins   Students     Time    Objective    Fraction         Gap          Status     Per student     Sizes')
    print(f'-'*240)
    
def tasks(args):
    case_num, num_muffins, num_students, lock, results_dict, status_dict, time_dict = args
    time_dict[case_num, 0] = datetime.now()
    try:
        model = setup_model(num_muffins, num_students)
        results = solve_model(model)
        write_solution, condition = check_solution(model, results)
        obj, gap = case_result(case_num, num_muffins, num_students, model, results, write_solution, condition, time_dict)
        results_dict[(num_muffins, num_students)] = obj
        if obj == -1:
            status_marker = '.'
        else:
            status_marker = '*' if condition == 'optimal' else '-'
        status_dict[(num_muffins, num_students)] = status_marker
    except Exception as e:
        print(f'Error in task {case_num}: {e}')

def print_summary(cases, ub_muffins, ub_students, results_dict, status_dict, time_start):
    print('\nSmallest piece for each case')
    print('============================')
    print('            Students')
    print(f'{'Muffins':<10}', end='')
    for num_students in range(1, ub_students+1):
        print(f'{num_students:>8}', end=' ')
    print()
    print('---------' * (ub_students+1))
    for num_muffins in range(1, ub_muffins+1):
        print(f'{num_muffins:<10}', end='')
        for num_students in range(1, ub_students+1):
            print(f'{str(to_fraction(results_dict[(num_muffins, num_students)])):>8}', end=' ')
        print()
    print()
    print('\nStatus for each case')
    print('====================')
    print('* = optimal, - = not optimal, . = no solution')
    print('            Students')
    print(f'{'Muffins':<10}', end='')
    for num_students in range(1, ub_students+1):
        print(f'{num_students:>8}', end=' ')
    print()
    print('---------' * (ub_students+1))
    for num_muffins in range(1, ub_muffins+1):
        print(f'{num_muffins:<10}', end='')
        for num_students in range(1, ub_students+1):
            print(f'{status_dict[(num_muffins, num_students)]:>8}', end=' ')
        print()
    time_end = datetime.now()
    time_elapsed = (time_end - time_start).total_seconds()
    time_total = sum((time_dict[i, 1] - time_dict[i, 0]).total_seconds() for i, case in enumerate(cases))
    print(f'\nElapsed time: {time_elapsed:.1f} seconds, total time {time_total:.1f} seconds\n')

def initialize_dicts(manager, ub_muffins, ub_students):
    results_dict = manager.dict()
    status_dict = manager.dict()
    time_dict = manager.dict()
    for num_muffins in range(1, ub_muffins + 1):
        for num_students in range(1, ub_students + 1):
            results_dict[(num_muffins, num_students)] = 0
            status_dict[(num_muffins, num_students)] = '.'
    return results_dict, status_dict, time_dict

def generate_cases(ub_muffins, ub_students):
    cases = [(num_muffins, num_students) for num_students in range(1, ub_students + 1) for num_muffins in range(num_students + 1, ub_muffins + 1)]
    return cases

if __name__ == '__main__':
    time_start = datetime.now()
    manager = mp.Manager()
    results_dict, status_dict, time_dict = initialize_dicts(manager, UB_MUFFINS, UB_STUDENTS)
    cases = generate_cases(UB_MUFFINS, UB_STUDENTS)
    lock = manager.Lock()
    pool = mp.Pool(processes=PROCESSES_TO_USE)  # Create a pool with the user-input number of processes
    pool.map(func=setup, iterable=[(UB_MUFFINS, UB_STUDENTS)])  # Do one-off setup
    try:
        results = pool.map_async(tasks, [(i, case[0], case[1], lock, results_dict, status_dict, time_dict) for i, case in enumerate(cases)])
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        pool.terminate()
        pool.join()
    print_summary(cases, UB_MUFFINS, UB_STUDENTS, results_dict, status_dict, time_start)