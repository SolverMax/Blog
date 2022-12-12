# Production mix - Model 10

# Import dependencies

import cvxpy as cp
import pandas as pd
import numpy as np
import os.path
import json

# Get data

DataFilename = os.path.join('.', 'productiondata10.json')
with open(DataFilename, 'r') as f:
    Data = json.load(f)
    
# Declarations

Name = Data['Name']
Hours = Data['Hours']
kg = Data['kg']
SalesLimit = Data['SalesLimit']
VarInitial = Data['VarInitial']   # Not used
VarLBounds = Data['VarLBounds']
VarUBounds = Data['VarUBounds']
Engine = Data['Engine']
TimeLimit = Data['TimeLimit']

Coefficients = Data['Coefficients']
Products = list(Coefficients.keys())
NumProducts = len(Products)

Margin = np.zeros(NumProducts)
People = np.zeros(NumProducts)
Materials = np.zeros(NumProducts)
Sales = np.zeros(NumProducts)
for p in Products:
    i = int(p)
    Margin[i]    = Coefficients[p]['Margin']
    People[i]    = Coefficients[p]['People']
    Materials[i] = Coefficients[p]['Materials']
    Sales[i]     = Coefficients[p]['Sales']
    
# Define model

Production = cp.Variable(NumProducts)   # Variables

objective = cp.Maximize(cp.sum(Margin @ Production))   # Objectve function
constraints = []   # Constraints
constraints += [cp.sum(People @ Production) <= Hours]
constraints += [cp.sum(Materials @ Production) <= kg]
constraints += [cp.sum(Sales @ Production) <= SalesLimit]

constraints += [Production >= VarLBounds]   # Bounds on variables
constraints += [Production <= VarUBounds]

# Solve model

Model = cp.Problem(objective, constraints)

if Engine == 'cbc':
    EngineObj = cp.CBC
elif Engine == 'glop':
    EngineObj = cp.GLOP
elif Engine == 'glpk':
    EngineObj = cp.GLPK
elif Engine == 'cvxopt':
    EngineObj = cp.CVXOPT

Result = Model.solve(solver=EngineObj, verbose=True, max_seconds=TimeLimit)

# Process results

WriteSolution = False
Optimal = False
Condition = Model.status

if Condition == 'optimal':
    Optimal = True
    WriteSolution = True
    
# Write output

print(Name, '\n')
print('Status:', Model.status)
print('Solver:', Engine, '\n')

if WriteSolution:
    print(f"Total margin = ${objective.value:,.2f}\n")
    pd.options.display.float_format = "{:,.4f}".format
    ProductResults = pd.DataFrame()
    for p in Products:
        ProductResults.loc[p, 'Production'] = Production[int(p)].value
    display(ProductResults)
    
    ConstraintStatus = pd.DataFrame(columns=['Slack', 'Dual'])
    for c in range(3):
        ConstraintStatus.loc[c] = [constraints[c].expr.value, constraints[c].dual_value]
    display(ConstraintStatus)
else:
    print('No solution loaded\n')
    print('Model:')
    print(Model)