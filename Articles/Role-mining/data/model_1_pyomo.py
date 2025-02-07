# Role mining model, Pyomo
# www.solvermax.com

from pyomo.environ import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from enum import Enum
import math
import os.path
import sys

DATA_FILE = 'data/firewall2.txt'
NUM_R = 10  # Number of roles to create
TIME_LIMIT = 600  # seconds
F_TYPE = 3  # 1 = security (remove only), 2 = availability (add only), 3 = noise (remove and add)
ENFORCE_ASSIGN = False  # Require at least 1 role for each user
os.environ['NEOS_EMAIL'] = 'myemail@example.com'  # Replace with your email address
WRITE_MODEL = False  # Write the model to an external file
NEOS = False  # True = Use NEOS Server, False = Use local solver

def create_permission_matrix():
    users_permissions = {}
    all_permissions = set()
    with open(DATA_FILE, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split()
                user = parts[0]
                permissions = [int(p[1:]) for p in parts[1:]]
                users_permissions[user] = permissions
                all_permissions.update(permissions)
    access = np.zeros((len(users_permissions), max(all_permissions) + 1))
    for i, permissions in enumerate(users_permissions.values()):
        access[i, permissions] = 1
    num_u, num_p = access.shape
    return access, num_u, num_p

def create_f_matrix(access, num_u, num_p):
    if F_TYPE == 1:  # Security: permissions may be removed but not added
        f_matrix = access
    elif F_TYPE == 2:  # Availability: permissions may be added but not removed
        f_matrix = 1 - access
    elif F_TYPE == 3:  # Noise: permissions may be removed and added
        f_matrix = np.ones((num_u, num_p))
    else:
        print(f'Invalid value for f matrix: {F_TYPE}')
        sys.exit(1)
    return f_matrix

def create_model(access, num_u, num_p, f_matrix):
    model = ConcreteModel()
    model.U = RangeSet(0, num_u - 1)
    model.P = RangeSet(0, num_p - 1)
    model.R = RangeSet(0, NUM_R - 1)
    model.assignment = Var(model.U, model.R, domain=Binary, initialize=0)
    model.definition = Var(model.R, model.P, domain=Binary, initialize=0)
    model.discrepancy = Var(model.U, model.P, domain=Binary, initialize=0)
    model.auxiliary = Var(model.U, model.P, model.R, domain=Binary, initialize=0)

    weights = [1, 0, 0]
    model.obj = Objective(
        expr=weights[0] * sum(model.discrepancy[u, p] for u in model.U for p in model.P) + \
             weights[1] * sum(model.definition[r, p] for r in model.R for p in model.P) + \
             weights[2] * sum(model.assignment[u, r] for u in model.U for r in model.R), sense=minimize)    
    
    model.constraints = ConstraintList()
    def add_constraints(model, u, p, r):
        if ENFORCE_ASSIGN:
            model.constraints.add(sum(model.assignment[u, r] for r in model.R) >= 1)  # Every user must have at least one role
        if math.isclose(f_matrix[u, p], 0) and math.isclose(access[u, p], 0):
            model.constraints.add(model.assignment[u, r] + model.definition[r, p] <= 1)  # Constraint (3)
        elif math.isclose(f_matrix[u, p], 0) and math.isclose(access[u, p], 1):
            model.constraints.add(model.auxiliary[u, p, r] <= model.assignment[u, r])  # Constraint (4)
            model.constraints.add(model.auxiliary[u, p, r] <= model.definition[r, p])  # Constraint (5)
            model.constraints.add(sum(model.auxiliary[u, p, r] for r in model.R) >= 1)  # Constraint (6)
        elif math.isclose(f_matrix[u, p], 1) and math.isclose(access[u, p], 0):
            model.constraints.add(model.assignment[u, r] + model.definition[r, p] <= 1 + model.discrepancy[u, p])  # Constraint (7)
        else:
            model.constraints.add(model.assignment[u, r] >= model.auxiliary[u, p, r])  # Constraint (8)
            model.constraints.add(model.definition[r, p] >= model.auxiliary[u, p, r])  # Constraint (9)
            model.constraints.add(sum(model.auxiliary[u, p, r] for r in model.R) >= 1 - model.discrepancy[u, p])  # Constraint (10)
    for u in model.U:
        for p in model.P:
            for r in model.R:
                add_constraints(model, u, p, r)
    return model

def write_model(model):
    if WRITE_MODEL:
        model.write('model.nl', io_options={'symbolic_solver_labels': False})
    
def solve_model(model):
    if NEOS:
        solver = SolverManagerFactory('neos')
        model.options = {'timelimit': TIME_LIMIT}
        results = solver.solve(model, load_solutions=True, tee=False, solver='cplex', options=model.options)
        print(results)
    else:  # Local solver
        solver = SolverFactory('appsi_highs')
        solver.options['time_limit'] = TIME_LIMIT
        solver.options['log_to_console'] = False
        solver.options['log_file'] = 'highs.log'
        results = solver.solve(model, load_solutions=True, tee=False)        
    status = results.solver.status + ', ' + results.solver.termination_condition
    return model, results, status
    
def process_results(model, num_u, num_p, access):
    assigned = np.zeros((num_u, num_p))
    result_added_matrix = np.zeros((num_u, num_p))
    result_removed_matrix = np.zeros((num_u, num_p))
    result_u_r = np.array([[round(value(model.assignment[u, r]), 0) for r in range(NUM_R)] for u in range(num_u)])
    result_r_p = np.array([[round(value(model.definition[r, p]), 0) for p in range(num_p)] for r in range(NUM_R)])
    
    for u in range(num_u):
        for p in range(num_p):
            assigned[u, p] = max(round(value(model.assignment[u, r]) * value(model.definition[r, p]), 0) for r in range(NUM_R))

    threshold = 0.5
    result_removed_list = [(u, p) for u in range(num_u) for p in range(num_p) 
        if access[u, p] > threshold and assigned[u, p] < 1 - threshold]
    result_added_list = [(u, p) for u in range(num_u) for p in range(num_p) 
        if access[u, p] < 1 - threshold and assigned[u, p] > threshold]
    result_removed_matrix[tuple(zip(*result_removed_list))] = 1
    result_added_matrix[tuple(zip(*result_added_list))] = 1
    result_obj = value(model.obj)
    result_discrepancy = np.array([[round(value(model.discrepancy[u, p], 0)) for p in range(num_p)] for u in range(num_u)])
    
    return result_u_r, result_r_p, result_discrepancy, result_added_matrix, result_removed_matrix, result_added_list, result_removed_list, result_obj

def print_results(num_u, access, result_u_r, result_r_p, result_added_list, result_removed_list, result_obj, status):
    print(f'\nAssignment of permissions to roles')
    for r in range(NUM_R):
        permissions = np.where(result_r_p[r])[0].tolist()
        print(f'Role {r}: Permissions {permissions}')
    print(f'\nAssignment of roles to users')
    for u in range(num_u):
        roles = np.where(result_u_r[u])[0].tolist()
        print(f'User {u}: Role {roles}')
    print(f'\nPermissions removed: {len(result_removed_list)}')
    for u, p in result_removed_list:
        print(f'User {u}, Permission {p}')
    print(f'\nPermissions added: {len(result_added_list)}')
    for u, p in result_added_list:
        print(f'User {u}, Permission {p}')
    print(f'\nActive roles: {NUM_R:,.0f}')
    print(f'Permission changes: {len(result_added_list) + len(result_removed_list)}')
    print(f'Objective: {result_obj:,.1f}')
    print(f'Status: {status}\n')

def create_heatmap(matrix, title, xlabel, ylabel, ax):
    rows, cols = matrix.shape
    ax.set_aspect('auto')
    sns.heatmap(matrix, ax=ax, cmap='YlOrRd', cbar=False, linewidths=0.5, linecolor='white', square=True)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(np.arange(0, cols, 5) + 0.5)
    ax.set_xticklabels(range(0, cols, 5))
    ax.set_yticks(np.arange(0, rows, 5) + 0.5)
    ax.set_yticklabels(range(0, rows, 5))
    ax.tick_params(axis='x', which='major', pad=7)
    ax.tick_params(axis='y', which='major', pad=7)

def visualize_results(access, result_u_r, result_r_p, result_discrepancy, result_added_matrix, result_removed_matrix):
    fig = plt.figure(figsize=(20, 30))
    gs = gridspec.GridSpec(3, 2, width_ratios=[1, 1], height_ratios=[1, 1, 0.5])

    def create_subplot(matrix, title, xlabel, ylabel, position, width, height):  # Create a subplot with specified size
        ax = plt.subplot(gs[position])
        create_heatmap(matrix, title, xlabel, ylabel, ax)
        ax.figure.set_size_inches(width, height)

    create_subplot(access, 'Original user-permission matrix', 'Permissions', 'Users', (0, 0), 9, 7.5)
    create_subplot(result_discrepancy, 'Discrepancy matrix', 'Permissions', 'Users', (0, 1), 9, 7.5)
    create_subplot(result_added_matrix, 'Permissions added', 'Permissions', 'Users', (1, 0), 9, 7.5)
    create_subplot(result_removed_matrix, 'Permissions removed', 'Permissions', 'Users', (1, 1), 9, 7.5)
    create_subplot(result_u_r.T, 'User-role matrix', 'Users', 'Roles', (2, 0), 6, 5)
    create_subplot(result_r_p, 'Role-permission matrix', 'Permissions', 'Roles', (2, 1), 6, 5)

    plt.tight_layout()
    plt.show()

def header(num_u, num_p):
    print(f'\nRole mining model, Pyomo')
    print(f'========================\n')
    print(f'Users: {num_u}\nPermissions: {num_p}\nRoles: {NUM_R}\n')

def main():
    access, num_u, num_p = create_permission_matrix()
    f_matrix = create_f_matrix(access, num_u, num_p)
    header(num_u, num_p)
    model = create_model(access, num_u, num_p, f_matrix)
    write_model(model)
    model, results, status = solve_model(model)
    result_u_r, result_r_p, result_discrepancy, result_added_matrix, result_removed_matrix, result_added_list, result_removed_list, result_obj = process_results(model, num_u, num_p, access)
    print_results(num_u, access, result_u_r, result_r_p, result_added_list, result_removed_list, result_obj, status)
    visualize_results(access, result_u_r, result_r_p, result_discrepancy, result_added_matrix, result_removed_matrix)

if __name__ == "__main__":
    main()
