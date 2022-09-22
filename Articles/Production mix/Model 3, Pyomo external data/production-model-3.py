# Production mix - Model 3

# Import dependencies

import pyomo.environ as pyo
import pandas as pd

# Import dependencies

import pyomo.environ as pyo
import pandas as pd

# Declarations

Model = pyo.ConcreteModel(name = Name)

# Define model

Model.Production = pyo.Var(Products, domain = pyo.NonNegativeReals, initialize = VarInitial, bounds = VarBounds)

Model.PeopleHours = pyo.Constraint(expr = sum(Coefficients[p]['People'] * Model.Production[p] for p in Products) <= Hours)
Model.MaterialUsage = pyo.Constraint(expr = sum(Coefficients[p]['Materials'] * Model.Production[p] for p in Products) <= kg)
Model.SalesRelationship = pyo.Constraint(expr = sum(Coefficients[p]['Sales'] * Model.Production[p] for p in Products) <= SalesLimit)

Model.TotalMargin = pyo.Objective(expr = sum(Coefficients[p]['Margin'] * Model.Production[p] for p in Products), sense = pyo.maximize)

# Solve model

Solver = pyo.SolverFactory(Engine)

if Engine == 'cbc':
    Solver.options['seconds'] = TimeLimit
elif Engine == 'glpk':
    Solver.options['tmlim'] = TimeLimit

Results = Solver.solve(Model, load_solutions = False, tee = False)

# Process results

WriteSolution = False
Optimal = False
LimitStop = False
Condition = Results.solver.termination_condition

if Condition == pyo.TerminationCondition.optimal:
    Optimal = True
if Condition == pyo.TerminationCondition.maxTimeLimit or Condition == pyo.TerminationCondition.maxIterations:
    LimitStop = True

if Optimal or LimitStop:
    try:
        WriteSolution = True
        Model.solutions.load_from(Results)                                     # Defer loading results until now, in case there is no solution to load
        SolverData = Results.Problem._list
        SolutionLB = SolverData[0].lower_bound
        SolutionUB = SolverData[0].upper_bound
    except:
        WriteSolution = False
        
# Write output

print(Model.name, '\n')
print('Status:', Results.solver.termination_condition)
print('Solver:', Engine, '\n')

if LimitStop:                                                                  # Indicate how close we are to a solution
    print('Objective bounds')
    print('----------------')
    if SolutionLB is None:
        print('Lower:      None')
    else:
        print(f'Lower: {SolutionLB:9,.2f}')
    if SolutionUB is None:
        print('Upper:      None\n')
    else:
        print(f'Upper: {SolutionUB:9,.2f}\n')
if WriteSolution:
    print(f'Total margin = ${Model.TotalMargin():,.2f}\n')
    ProductResults = pd.DataFrame()
    for p in Products:
        ProductResults.loc[p, 'Production'] = round(pyo.value(Model.Production[p]), 2)
    display(ProductResults)
else:
    print('No solution loaded\n')
    print('Model:')
    Model.pprint()
