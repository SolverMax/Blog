# Production mix - Model 8

# Import dependencies

from ortools.linear_solver import pywraplp
import pandas as pd
import os.path
import json

# Get data

DataFilename = os.path.join('.', 'productiondata8.json')
with open(DataFilename, 'r') as f:
    Data = json.load(f)

# Declarations

Model = pywraplp.Solver.CreateSolver(Data['Engine'])

Model.Name = Data['Name']
Model.Hours = Data['Hours']
Model.kg = Data['kg']
Model.VarInitial = Data['VarInitial']   # Not used
Model.VarLBounds = Data['VarLBounds']
Model.VarUBounds = Data['VarUBounds']
Model.Engine = Data['Engine']
Model.TimeLimit = Data['TimeLimit']

Model.SalesLimit = Data['SalesLimit']
Coefficients = Data['Coefficients']
Model.Products = list(Coefficients.keys())
Model.Production = {}

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

for p in Model.Products:
    Model.Production[p] = Model.NumVar(Model.VarLBounds, Model.VarUBounds, p)

Model.PeopleHours = Model.Add(sum(Model.People[p] * Model.Production[p] for p in Model.Products) <= Model.Hours, 'PeopleHours')
Model.MaterialUsage = Model.Add(sum(Model.Materials[p] * Model.Production[p] for p in Model.Products) <= Model.kg, 'MaterialUsage')
Model.SalesRelationship = Model.Add(sum(Model.Sales[p] * Model.Production[p] for p in Model.Products) <= Model.SalesLimit, 'SalesRelationship')
    
Model.TotalMargin = sum(Model.Margin[p] * Model.Production[p] for p in Model.Products)
Model.Maximize(Model.TotalMargin)

# Solve model

Model.set_time_limit(Model.TimeLimit)
Status = Model.Solve()

# Process results

WriteSolution = False
Optimal = False

if Status == pywraplp.Solver.OPTIMAL:
    Optimal = True
    WriteSolution = True
    StatusText = 'Optimal'
elif (Status == pywraplp.Solver.INFEASIBLE):
    StatusText = 'Infeasible'
elif (Status == pywraplp.Solver.UNBOUNDED):
    StatusText = 'Unbounded'
elif (Status == pywraplp.Solver.ABNORMAL): 
    StatusText = 'Abnormal'
elif (Status == pywraplp.Solver.NOT_SOLVED): 
    StatusText = 'Not solved'
    
# Write output

print(Model.Name, '\n')
print('Status:', StatusText)
print('Solver:', Model.Engine, '\n')

if WriteSolution:
    print(f"Total margin = ${Model.Objective().Value():,.2f}\n")
    pd.options.display.float_format = "{:,.4f}".format
    ProductResults = pd.DataFrame()
    for p in Model.Products:
        ProductResults.loc[p, 'Production'] = Model.Production[p].solution_value()
    display(ProductResults)

    ConstraintStatus = pd.DataFrame(columns=['Slack', 'Dual'])
    activities = Model.ComputeConstraintActivities()
    for i, constraint in enumerate(Model.constraints()):
        ConstraintStatus.loc[constraint.name()] = [constraint.ub() - activities[constraint.index()], constraint.dual_value()]
    display(ConstraintStatus)
else:
    print('No solution loaded\n')
    print('Model:')
    print(Model.ExportModelAsLpFormat(False).replace('\\', ' '))