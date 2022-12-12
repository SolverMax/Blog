# Production mix - Model 9

# Import dependencies

from gekko import GEKKO
import pandas as pd
import os.path
import json
import numpy as np

# Get data

DataFilename = os.path.join('.', 'productiondata9.json')
with open(DataFilename, 'r') as f:
    Data = json.load(f)
    
# Declarations

Model = GEKKO(name=Data['Name'], remote=False)

Model.Hours = Data['Hours']
Model.kg = Data['kg']
Model.SalesLimit = Data['SalesLimit']
Model.VarInitial = Data['VarInitial']   # Not used
Model.VarLBounds = Data['VarLBounds']
Model.VarUBounds = Data['VarUBounds']
Model.Engine = Data['Engine']
Model.TimeLimit = Data['TimeLimit']

Coefficients = Data['Coefficients']
Model.Products = Coefficients.keys()

Model.People = {}
Model.Materials = {}
Model.Sales = {}
Model.Margin = {}

for p in Model.Products:    
    Model.People[p] = Coefficients[p]['People']
    Model.Materials[p] = Coefficients[p]['Materials']
    Model.Sales[p] = Coefficients[p]['Sales']
    Model.Margin[p] = Coefficients[p]['Margin']
    
# Define model

Model.TotalMargin = Model.Var()
Model.Production  = dict(map(lambda p: (p, Model.Var(lb=Model.VarLBounds, ub=Model.VarUBounds)), Model.Products))

Model.PeopleHours = Model.Equation(sum(Model.People[p] * Model.Production[p] for p in Model.Products) <= Model.Hours)
Model.MaterialUsage = Model.Equation(sum(Model.Materials[p] * Model.Production[p] for p in Model.Products) <= Model.kg)
Model.SalesRelationship = Model.Equation(sum(Model.Sales[p] * Model.Production[p] for p in Model.Products) <= Model.SalesLimit)

Model.Equation(Model.TotalMargin == sum(Model.Margin[p] * Model.Production[p] for p in Model.Products))
Model.Maximize(Model.TotalMargin)

# Solve model

Model.options.MAX_TIME = Model.TimeLimit
Model.options.DIAGLEVEL = 2      # Enable extraction of dual prices

if Model.Engine == 'apopt':
    EngineNum = 1
elif Model.Engine == 'bpopt':
    EngineNum = 2
elif Model.Engine == 'ipopt':  # ipopt will be used if other solvers are not available
    EngineNum = 3

try:
    Success = True
    Model.solve(solver=EngineNum, linear=1, disp=True, debug=True)
except:
    Success = False
    
# Process results

WriteSolution = False
Optimal = False

if Success:
    Optimal = True
    WriteSolution = True
    StatusText = 'Optimal'
else:
    StatusText = 'Unsuccessful'
    
# Write output

print(Data['Name'],'\n')
print('Status:', StatusText)
print('Solver:', Model.Engine, '\n')

if WriteSolution:
    print(f"Total margin = ${Model.TotalMargin.value[0]:,.2f}\n")
    pd.options.display.float_format = "{:,.4f}".format
    ProductResults = pd.DataFrame()
    for p in Model.Products:
        ProductResults.loc[p, 'Production'] = Model.Production[p].value[0]
    display(ProductResults)
    
    ConstraintStatus = pd.DataFrame(columns=['Slack', 'Dual'])
    Duals = np.loadtxt(Model.path+'/apm_lam.txt')                       # Read dual prices from temporary folder
    ResultFilename = os.path.join(Model.path, 'results.json')
    with open(ResultFilename, 'r') as f:
        Results = json.load(f)                                          # Read slack values from temporary folder    
    for c in range(3):
        ConstraintStatus.loc[c] = [Results['slk_'+str(c+1)][0], Duals[c]]
    display(ConstraintStatus)    
else:
    print('No solution loaded\n')
    
Model.cleanup()          # Delete temporary folder