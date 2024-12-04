# Crop rotation model, created using Copilot
# www.solvermax.com

import pyomo.environ as pyo
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate
import csv

# Global constants
NUM_FIELDS = 8
NUM_SEASONS = 10
MAX_CROP_PER_FIELD = 4
DISCOUNT_RATE = 0.05
MAX_CROPS_PER_FIELD_PER_SEASON = 3
REPEAT_SEASON_1 = 9
REPEAT_SEASON_2 = 10
INITIAL_SEASON_1 = 1
INITIAL_SEASON_2 = 2
MAX_FALLOW_FIELDS_SEASON = 1
MAX_FALLOW_FIELDS_CYCLE = 1
BUDGET = 30000

# Define the model
def define_model():
    model = pyo.ConcreteModel()

    # Sets
    crops = ['corn', 'wheat', 'soybeans']
    fields = list(range(1, NUM_FIELDS + 1))
    seasons = list(range(1, NUM_SEASONS + 1))

    model.C = pyo.Set(initialize=crops)
    model.F = pyo.Set(initialize=fields)
    model.S = pyo.Set(initialize=seasons)

    # Parameters
    profit_per_tonne = {'corn': 100, 'wheat': 80, 'soybeans': 90}
    area = {f: 10 for f in fields}
    yield_per_hectare = {'corn': 10, 'wheat': 8, 'soybeans': 9}
    demand = {
        'corn': {1: 200, 2: 200, 3: 200, 4: 200, 5: 200, 6: 200, 7: 200, 8: 200, 9: 200, 10: 200},
        'wheat': {1: 90, 2: 70, 3: 60, 4: 50, 5: 60, 6: 70, 7: 80, 8: 90, 9: 80, 10: 70},
        'soybeans': {1: 100, 2: 100, 3: 100, 4: 100, 5: 100, 6: 100, 7: 100, 8: 100, 9:100, 10: 100}
    }
    
    cost = {'corn': 500, 'wheat': 400, 'soybeans': 450}

    # Variables
    model.x = pyo.Var(model.C, model.F, model.S, domain=pyo.Binary)
    model.fallow = pyo.Var(model.F, model.S, domain=pyo.Binary)

    # Objective function
    def objective_rule(model):
        return sum((profit_per_tonne[c] * model.x[c, f, s] * yield_per_hectare[c] * area[f] - cost[c] * model.x[c, f, s]) / ((1 + DISCOUNT_RATE) ** ((s-1)/2)) 
        for c in model.C for f in model.F for s in model.S)
    model.objective = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    # Constraints
    def planting_constraint_rule(model, f, s):
        return sum(model.x[c, f, s] for c in model.C)  + model.fallow[f, s] == 1
    model.planting_constraint = pyo.Constraint(model.F, model.S, rule=planting_constraint_rule)

    def rotation_constraint_rule(model, c, f, s):
        if s < max(model.S):
            return model.x[c, f, s] + model.x[c, f, s+1] <= 1
        else:
            return pyo.Constraint.Skip
    model.rotation_constraint = pyo.Constraint(model.C, model.F, model.S, rule=rotation_constraint_rule)

    def demand_constraint_rule(model, c, s):
        return sum(model.x[c, f, s] * yield_per_hectare[c] * area[f] for f in model.F) >= demand[c][s]
    model.demand_constraint = pyo.Constraint(model.C, model.S, rule=demand_constraint_rule)

    def budget_constraint_rule(model):
        return sum(cost[c] * model.x[c, f, s] / ((1 + DISCOUNT_RATE) ** ((s-1)/2)) for c in model.C for f in model.F for s in model.S) <= BUDGET
    model.budget_constraint = pyo.Constraint(rule=budget_constraint_rule)

    def adjacent_fields_different_crops_rule(model, c, f, s):
        if f < max(fields):
            return model.x[c, f, s] + model.x[c, f+1, s] <= 1
        else:
            return pyo.Constraint.Skip
    model.adjacent_fields_different_crops = pyo.Constraint(model.C, model.F, model.S, rule=adjacent_fields_different_crops_rule)

    def fallow_constraint_rule(model, f):
        return sum(model.fallow[f, s] for s in model.S) >= MAX_FALLOW_FIELDS_CYCLE
    model.fallow_constraint = pyo.Constraint(model.F, rule=fallow_constraint_rule)
    
    def max_fallow_fields_constraint_rule(model, s):
        return sum(model.fallow[f, s] for f in model.F) <= MAX_FALLOW_FIELDS_SEASON
    model.max_fallow_fields_constraint = pyo.Constraint(model.S, rule=max_fallow_fields_constraint_rule)

    def repeat_season_1_constraint_rule(model, c, f):
        return model.x[c, f, REPEAT_SEASON_1] == model.x[c, f, INITIAL_SEASON_1]
    model.repeat_season_1_constraint = pyo.Constraint(model.C, model.F, rule=repeat_season_1_constraint_rule)

    def repeat_season_2_constraint_rule(model, c, f):
        return model.x[c, f, REPEAT_SEASON_2] == model.x[c, f, INITIAL_SEASON_2]
    model.repeat_season_2_constraint = pyo.Constraint(model.C, model.F, rule=repeat_season_2_constraint_rule)

    def max_crop_per_field_constraint_rule(model, c, f):
        return sum(model.x[c, f, s] for s in model.S) <= MAX_CROP_PER_FIELD
    model.max_crop_per_field_constraint = pyo.Constraint(model.C, model.F, rule=max_crop_per_field_constraint_rule)

    return model, profit_per_tonne, area, yield_per_hectare, demand, fields, cost

# Solve the model
def solve_model(model):
    solver = pyo.SolverFactory('appsi_highs')
    results = solver.solve(model)
    return results

# Collect the results
def collect_results(model, profit_per_tonne, area, yield_per_hectare, demand, cost):
    solution = {f: {s: None for s in model.S} for f in model.F}
    season_profit = {s: 0 for s in model.S}
    total_profit = 0
    field_season_profit = {f: {s: 0 for s in model.S} for f in model.F}
    nominal_profit = {f: {s: 0 for s in model.S} for f in model.F}
    surplus = {c: {s: 0 for s in model.S} for c in model.C}
    production = {c: {s: 0 for s in model.S} for c in model.C}
    total_spend = 0
    
    for c in model.C:
        for f in model.F:
            for s in model.S:
                if pyo.value(model.x[c, f, s]) > 0.5:
                    solution[f][s] = c
                    nominal = (profit_per_tonne[c] * yield_per_hectare[c] * area[f]  - cost[c])
                    profit = nominal / ((1 + DISCOUNT_RATE) ** ((s-1)/2))
                    season_profit[s] += profit
                    total_profit += profit
                    field_season_profit[f][s] = profit
                    nominal_profit[f][s] = nominal
                    production[c][s] += yield_per_hectare[c] * area[f]
                    total_spend += cost[c] / ((1 + DISCOUNT_RATE) ** ((s-1)/2))
                    surplus[c][s] = production[c][s] - demand[c][s]
    total_profit -= total_spend
    
    return solution, season_profit, total_profit, field_season_profit, nominal_profit, surplus, production, total_spend
    
# Print the results
def print_results(model, solution, season_profit, total_profit, field_season_profit, nominal_profit, demand, production, surplus, total_spend):
    print(f"\nBudget: ${BUDGET:,.2f}")
    print(f"Total Spend: ${total_spend:,.2f}")
    
    # Crop planting plan
    crop_planting_plan = [["Field"] + [f"Season {s}" for s in model.S]]
    for f in model.F:
        crop_planting_plan.append([f] + [solution[f][s] if solution[f][s] else "-" for s in model.S])
    print("\nCrop planting plan (Field by Season):")
    print(tabulate(crop_planting_plan, headers="firstrow", tablefmt="grid", stralign="right", numalign="right"))

    # NPV profit
    npv_profit_table = [["Field"] + [f"Season {s}" for s in model.S] + ["Total"]]
    for f in model.F:
        row_total = sum(field_season_profit[f][s] for s in model.S)
        npv_profit_table.append([f] + [f"${field_season_profit[f][s]:,.2f}" for s in model.S] + [f"${row_total:,.2f}"])
    column_totals = [sum(field_season_profit[f][s] for f in model.F) for s in model.S]
    npv_profit_table.append(["Total"] + [f"${total:,.2f}" for total in column_totals] + [f"${total_profit:,.2f}"])
    print("\nNPV Profit from each field for each season:")
    print(tabulate(npv_profit_table, headers="firstrow", tablefmt="grid", stralign="right", numalign="right"))

    # Nominal profit
    nominal_profit_table = [["Field"] + [f"Season {s}" for s in model.S] + ["Total"]]
    for f in model.F:
        row_total = sum(nominal_profit[f][s] for s in model.S)
        nominal_profit_table.append([f] + [f"${nominal_profit[f][s]:,.2f}" for s in model.S] + [f"${row_total:,.2f}"])
    column_totals_nominal = [sum(nominal_profit[f][s] for f in model.F) for s in model.S]
    nominal_profit_table.append(["Total"] + [f"${total:,.2f}" for total in column_totals_nominal] + [f"${sum(column_totals_nominal):,.2f}"])
    print("\nNominal Profit from each field for each season:")
    print(tabulate(nominal_profit_table, headers="firstrow", tablefmt="grid", stralign="right", numalign="right"))

    # Demand
    demand_table = [["Crop"] + [f"Season {s}" for s in model.S]]
    for c in model.C:
        demand_table.append([c] + [f"{demand[c][s]:,.2f}" for s in model.S])
    print("\nDemand for each crop each season:")
    print(tabulate(demand_table, headers="firstrow", tablefmt="grid", stralign="right", numalign="right"))
    
    # Production
    production_table = [["Crop"] + [f"Season {s}" for s in model.S]]
    for c in model.C:
        production_table.append([c] + [f"{production[c][s]:,.2f}" for s in model.S])
    print("\nProduction of each crop each season:")
    print(tabulate(production_table, headers="firstrow", tablefmt="grid", stralign="right", numalign="right"))
    
    # Surplus of production in excess of demand
    surplus_table = [["Crop"] + [f"Season {s}" for s in model.S]]
    for c in model.C:
        surplus_table.append([c] + [f"{surplus[c][s]:,.2f}" for s in model.S])
    print("\nSurplus of production in excess of demand (Crop by Season):")
    print(tabulate(surplus_table, headers="firstrow", tablefmt="grid", stralign="right", numalign="right"))

    # Write results to CSV
    write_results_to_csv(crop_planting_plan, npv_profit_table, nominal_profit_table, demand_table, production_table, surplus_table, total_spend)

def write_results_to_csv(crop_planting_plan, npv_profit_table, nominal_profit_table, demand_table, production_table, surplus_table, total_spend):
    with open('results.csv', mode='w', newline='') as file:
        writer = csv.writer(file)

        writer.writerow(["Budget and Total Spend"])
        writer.writerow(["Budget", f"${BUDGET:,.2f}"])
        writer.writerow(["Total Spend", f"${total_spend:,.2f}"])
        writer.writerow([])
        
        writer.writerow(["Crop Planting Plan"])
        writer.writerows(crop_planting_plan)
        writer.writerow([])

        writer.writerow(["NPV Profit"])
        writer.writerows(npv_profit_table)
        writer.writerow([])

        writer.writerow(["Nominal Profit"])
        writer.writerows(nominal_profit_table)
        writer.writerow([])

        writer.writerow(["Demand for Each Crop Each Season"])
        writer.writerows(demand_table)
        writer.writerow([])

        writer.writerow(["Production of Each Crop Each Season"])
        writer.writerows(production_table)
        writer.writerow([])
        
        writer.writerow(["Surplus of Production"])
        writer.writerows(surplus_table)

    print("\nResults have been written to 'results.csv'")
    
# Plot the results
def plot_results(model, solution, fields):
    fig, ax = plt.subplots()
    y_labels = [f"Field {f}" for f in reversed(fields)]
    y_pos = np.arange(len(y_labels))
    bar_width = 0.8

    colors = {'corn': 'yellow', 'wheat': 'brown', 'soybeans': 'green', 'fallow': 'gray'}
    labels = {'corn': 'Corn', 'wheat': 'Wheat', 'soybeans': 'Soybeans', 'fallow': 'Fallow'}
    
    # Plot the bars
    for i, f in enumerate(reversed(model.F)):
        for s in model.S:
            crop = solution[f][s] if solution[f][s] else 'fallow'
            ax.barh(i, 1, left=s-1, height=bar_width, color=colors[crop], edgecolor='black')

    # Add all possible labels to the legend
    handles = [plt.Rectangle((0,0),1,1, color=colors[crop]) for crop in colors]
    ax.legend(handles, [labels[crop] for crop in colors], loc='center left', bbox_to_anchor=(1, 0.5))

    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel('Seasons')
    ax.set_title('Optimal Crop Rotation Plan')
    plt.tight_layout(rect=[0, 0, 0.85, 1])  # Adjust layout to make room for the legend
    plt.show()
    
# Main function
def main():
    model, profit_per_tonne, area, yield_per_hectare, demand, fields, cost = define_model()
    results = solve_model(model)
    if results.solver.termination_condition == pyo.TerminationCondition.infeasible:
        print("The problem is infeasible. Please check the constraints and parameters.")
    else:
        solution, season_profit, total_profit, field_season_profit, nominal_profit, surplus, production, total_spend = collect_results(model, profit_per_tonne, area, yield_per_hectare, demand, cost)
        print_results(model, solution, season_profit, total_profit, field_season_profit, nominal_profit, demand, production, surplus, total_spend)
        plot_results(model, solution, fields)

if __name__ == "__main__":
    main()