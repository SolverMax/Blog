# Production mix - Model 7

# Import dependencies

import pulp as pu
import pandas as pd
import os.path
import json

# Get data

DataFilename = os.path.join('.', 'productiondata7.json')
with open(DataFilename, 'r') as f:
    Data = json.load(f)
    
# Declarations

Model = pu.LpProblem(Data['Name'], pu.LpMaximize)

Model.Hours = Data['Hours']
Model.kg = Data['kg']
Model.SalesLimit = Data['SalesLimit']
Model.VarInitial = Data['VarInitial']
Model.VarLBounds = Data['VarLBounds']
Model.VarUBounds = Data['VarUBounds']
Model.Engine = Data['Engine']
Model.TimeLimit = Data['TimeLimit']

Coefficients = Data['Coefficients']
Model.Products = list(Coefficients.keys())

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

Model.Production = pu.LpVariable.dicts("Products", Model.Products, lowBound=Model.VarLBounds, upBound=Model.VarUBounds, cat=pu.LpContinuous)
for p in Model.Products:
    Model.Production[p].setInitialValue(Model.VarInitial)

def constraint_hours():
    return pu.lpSum([Model.People[p] * Model.Production[p] for p in Model.Products]) <= Model.Hours, 'PeopleHours'
Model += constraint_hours()

def constraint_usage():
    return pu.lpSum([Model.Materials[p] * Model.Production[p] for p in Model.Products]) <= Model.kg, 'MaterialUsage'
Model += constraint_usage()

def constraint_sales():
    return pu.lpSum([Model.Sales[p] * Model.Production[p] for p in Model.Products]) <= Model.SalesLimit, 'SalesRelationship'
Model += constraint_sales()

def objective_margin():
    return pu.lpSum([Model.Margin[p] * Model.Production[p] for p in Model.Products])
Model.setObjective(objective_margin())

# Solve model

if Model.Engine == 'cbc':
    Solver = pu.PULP_CBC_CMD(timeLimit = Model.TimeLimit)
elif Model.Engine == 'glpk':
    Solver = pu.GLPK_CMD(timeLimit = Model.TimeLimit)

Status = Model.solve(Solver)

# Process results

WriteSolution = False
Optimal = False
Condition = pu.LpStatus[Model.status]

if Condition == 'Optimal':
    Optimal = True
    WriteSolution = True
    
# Write output

print(Model.name, '\n')
print('Status:', pu.LpStatus[Model.status])
print('Solver:', Model.Engine, '\n')

if WriteSolution:
    print(f"Total margin = ${Model.objective.value():,.2f}\n")
    pd.options.display.float_format = "{:,.4f}".format
    ProductResults = pd.DataFrame()
    for p in Model.Products:
        ProductResults.loc[p, 'Production'] = pu.value(Model.Production[p])
    display(ProductResults)

    ConstraintStatus = pd.DataFrame(columns=['Slack', 'Dual'])
    for name, c in list(Model.constraints.items()):
        ConstraintStatus.loc[name] = [c.slack, c.pi]
    display(ConstraintStatus)
else:
    print('No solution loaded\n')
    print('Model:')
    print(Model)