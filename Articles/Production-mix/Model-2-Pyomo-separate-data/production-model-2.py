# Production mix - Model 2

# Import dependencies

import pyomo.environ as pyo
import pandas as pd

# Declarations

Model = pyo.ConcreteModel(name = 'Boutique pottery shop - Model 2')

Hours = 250
kg = 500
SalesLimit = 0

Coefficients = {
    'Discs' : {'People': 12.50, 'Materials': 18.00, 'Sales': -2.00, 'Margin':  80.00},  
    'Orbs'  : {'People': 10.00, 'Materials': 30.00, 'Sales':  1.00, 'Margin': 200.00},
}

Products = Coefficients.keys()

VarInitial = 0
VarBounds = (0, 100)

# Declarations

Model = pyo.ConcreteModel(name = 'Boutique pottery shop - Model 2')

Hours = 250
kg = 500
SalesLimit = 0

Coefficients = {
    'Discs' : {'People': 12.50, 'Materials': 18.00, 'Sales': -2.00, 'Margin':  80.00},  
    'Orbs'  : {'People': 10.00, 'Materials': 30.00, 'Sales':  1.00, 'Margin': 200.00},
}

Products = Coefficients.keys()

VarInitial = 0
VarBounds = (0, 100)

# Solve model

Solver = pyo.SolverFactory('cbc')
Results = Solver.solve(Model)

# Write output

print(Model.name, '\n')
print('Status: ', Results.solver.status, '\n')
print(f'Total margin = ${Model.TotalMargin():,.2f}\n')
ProductResults = pd.DataFrame()
for p in Products:
    ProductResults.loc[p, 'Production'] = round(pyo.value(Model.Production[p]), 2)
display(ProductResults)
