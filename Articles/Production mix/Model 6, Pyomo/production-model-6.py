# Production mix - Model 6

# Import dependencies

import pyomo.environ as pyo
import pandas as pd

# Declarations

Model = pyo.AbstractModel()

Model.Products = pyo.Set()                                                         # Pyomo Set rather than Python set

Model.Name = pyo.Param(within = pyo.Any)
Model.Hours = pyo.Param(within = pyo.NonNegativeReals)
Model.kg = pyo.Param(within = pyo.NonNegativeReals)
Model.SalesLimit = pyo.Param(within = pyo.NonNegativeReals)
Model.VarInitial = pyo.Param(within = pyo.NonNegativeReals)
Model.VarLBounds = pyo.Param(within = pyo.NonNegativeReals)
Model.VarUBounds = pyo.Param(within = pyo.NonNegativeReals)
Model.Engine = pyo.Param(within = pyo.Any)
Model.TimeLimit = pyo.Param(within = pyo.NonNegativeReals)
Model.People = pyo.Param(Model.Products, within = pyo.NonNegativeReals) 
Model.Materials = pyo.Param(Model.Products, within = pyo.NonNegativeReals)
Model.Sales = pyo.Param(Model.Products, within = pyo.Reals)
Model.Margin = pyo.Param(Model.Products, within = pyo.Reals)

# Define model

Model.Production = pyo.Var(Model.Products, domain = pyo.NonNegativeReals, initialize = Model.VarInitial, bounds = (Model.VarLBounds, Model.VarUBounds))

def rule_hours(Model):
    return sum(Model.People[p] * Model.Production[p] for p in Model.Products) <= Model.Hours
Model.PeopleHours = pyo.Constraint(rule = rule_hours)

def rule_usage(Model):
    return sum(Model.Materials[p] * Model.Production[p] for p in Model.Products) <= Model.kg
Model.MaterialUsage = pyo.Constraint(rule = rule_usage)

def rule_sales(Model):
    return sum(Model.Sales[p] * Model.Production[p] for p in Model.Products) <= Model.SalesLimit
Model.SalesRelationship = pyo.Constraint(rule = rule_sales)

def rule_Obj(Model):
    return sum(Model.Margin[p] * Model.Production[p] for p in Model.Products)
Model.TotalMargin = pyo.Objective(rule = rule_Obj, sense = pyo.maximize)

# Solve model

Instance = Model.create_instance("productiondata6.dat")
Solver = pyo.SolverFactory(pyo.value(Instance.Engine))
if pyo.value(Instance.Engine) == 'cbc':
    Solver.options['seconds'] = pyo.value(Instance.TimeLimit)
elif pyo.value(Instance.Engine) == 'glpk':
    Solver.options['tmlim'] = pyo.value(Instance.TimeLimit)
    
Instance.dual = pyo.Suffix(direction = pyo.Suffix.IMPORT)

Results = Solver.solve(Instance, load_solutions = False, tee = False)

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
        Instance.solutions.load_from(Results)
        SolverData = Results.Problem._list
        SolutionLB = SolverData[0].lower_bound
        SolutionUB = SolverData[0].upper_bound
    except:
        WriteSolution = False
        
# Write output

print(pyo.value(Instance.Name), '\n')
print('Status:', Results.solver.termination_condition)
print('Solver:', pyo.value(Instance.Engine), '\n')

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
    print(f'Total margin = ${Instance.TotalMargin():,.2f}\n')
    pd.options.display.float_format = "{:,.4f}".format
    ProductResults = pd.DataFrame()
    for p in Instance.Products:
        ProductResults.loc[p, 'Production'] = round(pyo.value(Instance.Production[p]), 4)
    display(ProductResults)
    
    ConstraintStatus = pd.DataFrame(columns=['lSlack', 'uSlack', 'Dual'])
    for c in Instance.component_objects(pyo.Constraint, active = True):
        ConstraintStatus.loc[c.name] = [c.lslack(), c.uslack(), Instance.dual[c]]
    display(ConstraintStatus)
else:
    print('No solution loaded\n')
    print('Model:')
    Instance.pprint()