# Production mix - Model 4

# Import dependencies

import pyomo.environ as pyo
import pandas as pd
import os.path
import json

# Get data

DataFilename = os.path.join('.', 'productiondata4.json')
with open(DataFilename, 'r') as f:
    Data = json.load(f)

# Declarations

Model = pyo.ConcreteModel(name = Data['Name'])

Model.Hours = pyo.Param(within = pyo.NonNegativeReals, initialize = Data['Hours'])
Model.kg = pyo.Param(within = pyo.NonNegativeReals, initialize = Data['kg'])
Model.SalesLimit = pyo.Param(within = pyo.NonNegativeReals, initialize = Data['SalesLimit'])
Model.VarInitial = pyo.Param(within = pyo.NonNegativeReals, initialize = Data['VarInitial'])
Model.VarLBounds = pyo.Param(within = pyo.NonNegativeReals, initialize = Data['VarLBounds'])
Model.VarUBounds = pyo.Param(within = pyo.NonNegativeReals, initialize = Data['VarUBounds'])
Model.Engine = pyo.Param(within = pyo.Any, initialize = Data['Engine'])
Model.TimeLimit = pyo.Param(within = pyo.NonNegativeReals, initialize = Data['TimeLimit'])

Coefficients = Data['Coefficients']
Model.Products = pyo.Set(initialize = list(Coefficients.keys()))                 # Pyomo Set rather than Python set

Model.People = pyo.Param(Model.Products, within = pyo.NonNegativeReals, mutable = True)
Model.Materials = pyo.Param(Model.Products, within = pyo.NonNegativeReals, mutable = True)
Model.Sales = pyo.Param(Model.Products, within = pyo.Reals, mutable = True)
Model.Margin = pyo.Param(Model.Products, within = pyo.Reals, mutable = True)

for p in Model.Products:    
    Model.People[p] = Coefficients[p]['People']
    Model.Materials[p] = Coefficients[p]['Materials']
    Model.Sales[p] = Coefficients[p]['Sales']
    Model.Margin[p] = Coefficients[p]['Margin']

# Define model

Model.Production = pyo.Var(Model.Products, domain = pyo.NonNegativeReals, initialize = Model.VarInitial, bounds = (Model.VarLBounds, Model.VarUBounds))

Model.PeopleHours = pyo.Constraint(expr = sum(Model.People[p] * Model.Production[p] for p in Model.Products) <= Model.Hours)
Model.MaterialUsage = pyo.Constraint(expr = sum(Model.Materials[p] * Model.Production[p] for p in Model.Products) <= Model.kg)
Model.SalesRelationship = pyo.Constraint(expr = sum(Model.Sales[p] * Model.Production[p] for p in Model.Products) <= Model.SalesLimit)

Model.TotalMargin = pyo.Objective(expr = sum(Model.Margin[p] * Model.Production[p] for p in Model.Products), sense = pyo.maximize)

# Solve model

Solver = pyo.SolverFactory(pyo.value(Model.Engine))

if pyo.value(Model.Engine) == 'cbc':
    Solver.options['seconds'] = pyo.value(Model.TimeLimit)
elif pyo.value(Model.Engine) == 'glpk':
    Solver.options['tmlim'] = pyo.value(Model.TimeLimit)
    
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
print('Solver:', pyo.value(Model.Engine), '\n')

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
    for p in Model.Products:
        ProductResults.loc[p, 'Production'] = round(pyo.value(Model.Production[p]), 2)
    display(ProductResults)
else:
    print('No solution loaded\n')
    print('Model:')
    Model.pprint()    
