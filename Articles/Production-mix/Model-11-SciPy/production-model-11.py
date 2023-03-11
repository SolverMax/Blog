# Production mix - Model 11

# Import dependencies

from scipy.optimize import linprog
import pandas as pd
import numpy as np
import os.path
import json

# Get data

DataFilename = os.path.join('.', 'productiondata11.json')
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

# Define model

Margin = np.zeros(NumProducts)
People = np.zeros(NumProducts)
Materials = np.zeros(NumProducts)
Sales = np.zeros(NumProducts)
for p in Products:
    i = int(p)-1
    Margin[i]    = -Coefficients[p]['Margin']  # Need to negate, as SciPy always minimizes, but we want to maximize
    People[i]    =  Coefficients[p]['People']
    Materials[i] =  Coefficients[p]['Materials']
    Sales[i]     =  Coefficients[p]['Sales']
    
ObJCoeff = Margin
Constraints = [People, Materials, Sales]
rhs = [Hours, kg, SalesLimit]

# Solve model

Model = linprog(c = ObJCoeff, A_ub = Constraints, b_ub = rhs, bounds = [(VarLBounds, VarUBounds)], method = Engine, options = {'time_limit': TimeLimit})

# Process results

WriteSolution = False
Optimal = False
Condition = Model.success

if Condition:
    Optimal = True
    WriteSolution = True
    
# Write output

print(Name, '\n')
print('Status: ', Model.success, '\n')

if WriteSolution:
    print(f"Total margin = ${-Model.fun:,.2f}\n")  # Need to negate, as we're maximizing
    pd.options.display.float_format = "{:,.4f}".format
    ProductResults = pd.DataFrame()
    for p in Products:
        ProductResults.loc[p, 'Production'] = Model.x[int(p)-1]
    display(ProductResults)
    ConstraintStatus = pd.DataFrame(columns=['Slack', 'Dual'])
    for c in range(len(Constraints)):
        ConstraintStatus.loc[c] = [Model.slack[c], Model['ineqlin']['marginals'][c]]
    display(ConstraintStatus)
else:
    print('No solution loaded\n')
    print('Model:')
    print(Model)