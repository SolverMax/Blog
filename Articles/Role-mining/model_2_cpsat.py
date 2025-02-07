# Role mining model, CP-SAT
# www.solvermax.com

from ortools.sat.python import cp_model
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from enum import Enum
import math
import time
import threading

DATA_FILE = 'data/firewall2.txt'
NUM_R = 10  # Number of roles to create
TIME_LIMIT = 3600  # seconds
F_TYPE = 3  # 1 = remove only, 2 = add only, 3 = remove and add
ENFORCE_ASSIGN = False  # Require at least 1 role for each user

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
    model = cp_model.CpModel()
    assignment = {}
    definition = {}
    discrepancy = {}
    auxiliary = {}
    for u in range(num_u):
        for r in range(NUM_R):
            assignment[u, r] = model.NewBoolVar(f'assignment_{u}_{r}')
        for p in range(num_p):
            discrepancy[u, p] = model.NewBoolVar(f'discrepancy_{u}_{p}')
            for r in range(NUM_R):
                auxiliary[u, p, r] = model.NewBoolVar(f'auxiliary_{u}_{p}_{r}')
    for r in range(NUM_R):
        for p in range(num_p):
            definition[r, p] = model.NewBoolVar(f'definition_{r}_{p}')

    weights = [1, 0, 0]
    model.Minimize(weights[0] * sum(discrepancy[u, p] for u in range(num_u) for p in range(num_p)) \
                 + weights[1] * sum(definition[r, p] for r in range(NUM_R) for p in range(num_p)) \
                 + weights[2] * sum(assignment[u, r] for u in range(num_u) for r in range(NUM_R)))
 
    for u in range(num_u):
        for p in range(num_p):
            for r in range(NUM_R):
                if ENFORCE_ASSIGN:
                    model.Add(sum(assignment[u, r] for r in range(NUM_R)) >= 1)  # Every user must have at least one role
                if math.isclose(f_matrix[u, p], 0) and math.isclose(access[u, p], 0):
                    model.Add(assignment[u, r] + definition[r, p] <= 1)  # Constraint (3)
                elif math.isclose(f_matrix[u, p], 0) and math.isclose(access[u, p], 1):
                    model.Add(auxiliary[u, p, r] <= assignment[u, r])  # Constraint (4)
                    model.Add(auxiliary[u, p, r] <= definition[r, p])  # Constraint (5)
                    model.Add(sum(auxiliary[u, p, r] for r in range(NUM_R)) >= 1)  # Constraint (6)
                elif math.isclose(f_matrix[u, p], 1) and math.isclose(access[u, p], 0):
                    model.Add(assignment[u, r] + definition[r, p] <= 1 + discrepancy[u, p])  # Constraint (7)
                else:
                    model.Add(assignment[u, r] >= auxiliary[u, p, r])  # Constraint (8)
                    model.Add(definition[r, p] >= auxiliary[u, p, r])  # Constraint (9)
                    model.Add(sum(auxiliary[u, p, r] for r in range(NUM_R)) >= 1 - discrepancy[u, p])  # Constraint (10)
    
    return model, assignment, definition, discrepancy, auxiliary

def solve_model(model):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TIME_LIMIT
    objective_logger = ObjectiveLogger(print_interval=5)
    status = solver.Solve(model, objective_logger)
    objective_logger.stop()
    return solver, status

class ObjectiveLogger(cp_model.CpSolverSolutionCallback):
    def __init__(self, print_interval=5):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._start_time = time.time()
        self._print_interval = print_interval
        self._last_objective = float('inf')
        self._stop_flag = False
        self._thread = threading.Thread(target=self._print_objective)
        self._thread.start()

    def on_solution_callback(self):
        self._last_objective = self.ObjectiveValue()

    def _print_objective(self):
        while not self._stop_flag:
            current_time = time.time() - self._start_time
            print(f'{current_time:>6,.0f}  {self._last_objective:>8,.0f}')
            time.sleep(self._print_interval)

    def stop(self):
        self._stop_flag = True
        self._thread.join()
        
def process_results(solver, num_u, num_p, access, assignment, definition, auxiliary, discrepancy, status_num):
    assigned = np.zeros((num_u, num_p))
    result_added_matrix = np.zeros((num_u, num_p))
    result_removed_matrix = np.zeros((num_u, num_p))
    result_u_r = np.array([[solver.BooleanValue(assignment[u, r]) for r in range(NUM_R)] for u in range(num_u)])
    result_r_p = np.array([[solver.BooleanValue(definition[r, p]) for p in range(num_p)] for r in range(NUM_R)])

    for u in range(num_u):
        for p in range(num_p):
            assigned[u, p] = max(solver.BooleanValue(assignment[u, r]) * solver.BooleanValue(definition[r, p]) for r in range(NUM_R))

    threshold = 0.5
    result_removed_list = [(u, p) for u in range(num_u) for p in range(num_p) 
        if access[u, p] > threshold and assigned[u, p] < 1 - threshold]
    result_added_list = [(u, p) for u in range(num_u) for p in range(num_p) 
        if access[u, p] < 1 - threshold and assigned[u, p] > threshold]
    result_removed_matrix[tuple(zip(*result_removed_list))] = 1
    result_added_matrix[tuple(zip(*result_added_list))] = 1
    result_obj = solver.ObjectiveValue()
    result_discrepancy = np.array([[solver.BooleanValue(discrepancy[u, p]) for p in range(num_p)] for u in range(num_u)])
    status = solver.status_name(status_num)
    return result_u_r, result_r_p, result_discrepancy, result_added_matrix, result_removed_matrix, result_added_list, result_removed_list, result_obj, status

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
    print(f'\nRole mining model, CP-SAT')
    print(f'=========================\n')
    print(f'Users: {num_u}\nPermissions: {num_p}\nRoles: {NUM_R}\n')
    print('  Time      Best')
    print('----------------')

def main():
    access, num_u, num_p = create_permission_matrix()
    f_matrix = create_f_matrix(access, num_u, num_p)
    header(num_u, num_p)
    model, assignment, definition, discrepancy, auxiliary \
        = create_model(access, num_u, num_p, f_matrix)
    solver, status = solve_model(model)
    result_u_r, result_r_p, result_discrepancy, result_added_matrix, result_removed_matrix, result_added_list, result_removed_list, result_obj, status_name \
        = process_results(solver, num_u, num_p, access, assignment, definition, auxiliary, discrepancy, status)
    print_results(num_u, access, result_u_r, result_r_p, result_added_list, result_removed_list, result_obj, status_name)
#    visualize_results(access, result_u_r, result_r_p, result_discrepancy, result_added_matrix, result_removed_matrix)

if __name__ == "__main__":
    main()