# Production mix - Model 1

# Import dependencies

import pyomo.environ as pyo

# Declarations

Model = pyo.ConcreteModel(name = 'Boutique pottery shop - Model 1')

# Define model

Model.Discs = pyo.Var(domain = pyo.NonNegativeReals)
Model.Orbs = pyo.Var(domain = pyo.NonNegativeReals)

Model.PeopleHours = pyo.Constraint(expr = 12.50 * Model.Discs + 10.00 * Model.Orbs <= 250)
Model.MaterialUsage = pyo.Constraint(expr = 18.00 * Model.Discs + 30.00 * Model.Orbs <= 500)
Model.SalesRelationship = pyo.Constraint(expr = -2.00 * Model.Discs + 1.00 * Model.Orbs <= 0)

Model.TotalMargin = pyo.Objective(expr = 80.00 * Model.Discs + 200.00 * Model.Orbs, sense = pyo.maximize)

# Solve model

Solver = pyo.SolverFactory('cbc')
Results = Solver.solve(Model)

# Write output

print(Model.name, '\n')
print('Status: ', Results.solver.status, '\n')
print(f'Total margin = ${Model.TotalMargin():,.2f}')
print(f'Production of discs = {Model.Discs():6.2f}')
print(f'Production of orbs  = {Model.Orbs():6.2f}')