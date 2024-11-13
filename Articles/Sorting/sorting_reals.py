# Sorting using a MIP model
# www.solvermax.com

import random
import pyomo.environ as pyo
import time

OBJ_CHOICE = 2  # Choose objective = [1, 2]
EXTRA_CONSTRAINT = False  # Include extra constraint
PRINT_RESULT = False  # Print detailed result. Useful for testing, otherwise False
TIME_LIMIT = 8*3600  # seconds
N_START = 50  # Start value for number of items to sort
N_END = 225  # End value for number of items to sort
N_STEP = 25  # Step value for number of items to sort

def generate_unique_random_set(n):  # Generate a unique set of unsorted random values from 1 to n
    random.seed(42)  # Specify random seed, so each method gets the same unsorted list
    p = []
    for i in range(0, n):
        x = random.random()
        p.append(x)
    return p

def create_model(n):
    p = generate_unique_random_set(n)
    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(1, n)
    model.p = pyo.Param(model.I, mutable=True)
    model.x = pyo.Var(model.I, model.I, domain=pyo.Binary)
    model.y = pyo.Var(model.I, domain=pyo.NonNegativeReals)

    for i in model.I:
        model.p[i] = p[i-1]  # Assign data to Pyomo object to align indices (p index 0..i-1, model.p index 1..i)
        
    if OBJ_CHOICE == 1:
        model.obj = pyo.Objective(expr=0, sense=pyo.minimize)
    elif OBJ_CHOICE == 2:
        model.obj = pyo.Objective(expr=sum(model.y[i] * i for i in model.I), sense=pyo.maximize)
    else:
        print('Invalid objective function number')
    
    model.cons = pyo.ConstraintList()
    for j in model.I:
        model.cons.add(sum(model.x[i, j] for i in model.I) == 1)

    for i in model.I:
        model.cons.add(sum(model.x[i, j] for j in model.I) == 1)
        model.cons.add(model.y[i] == sum(model.x[i, j] * model.p[j] for j in model.I))
        if i >= 2:
            model.cons.add(model.y[i] >= model.y[i-1])

    if EXTRA_CONSTRAINT:
        model.cons.add(sum(model.y[i] for i in model.I) == sum(model.p[i] for i in model.I))

    return model

def header():
    print('\nSorting using a MIP model')
    print('=========================')
    print(f'Objective {OBJ_CHOICE}, extra constraint {EXTRA_CONSTRAINT}\n')

def create_solver():
    solver = pyo.SolverFactory('appsi_highs')
    solver.options['log_file'] = 'highs.log'
    solver.options['time_limit'] = TIME_LIMIT
    return solver

def solve_model(solver, model):
    start_time = time.time()
    result = solver.solve(model, load_solutions=False, tee=False)
    end_time = time.time()
    status = 'OK' if result.solver.status == pyo.SolverStatus.ok else 'No solution'
    return result, status, end_time - start_time

def print_results(model):
    if PRINT_RESULT:
        print('\nItem   Original   Sorted')
        print('------------------------')
        for i in model.I:
            print(f' {i:>3}     {pyo.value(model.p[i]):>6,.4f}   {(pyo.value(model.y[i])):>6,.4f}')
        print()
        
def main():
    header()
    for n in range(N_START, N_END + N_STEP, N_STEP):
        model = create_model(n)
        solver = create_solver()
        result, status, elapsed_time = solve_model(solver, model)
        if status == 'OK':
            model.solutions.load_from(result)
            print_results(model)
        print(f'n = {n:>4,}, time = {elapsed_time:>7,.1f} seconds, status = {status}')

if __name__ == "__main__":
    main()