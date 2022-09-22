Name  = 'Boutique pottery shop - Model 3'
Hours = 250
kg    = 500
SalesLimit = 0

Coefficients = {
    'Discs' : {'People': 12.50, 'Materials': 18.00, 'Sales': -2.00, 'Margin':  80.00},  
    'Orbs'  : {'People': 10.00, 'Materials': 30.00, 'Sales':  1.00, 'Margin': 200.00}
}
Products = Coefficients.keys()

VarInitial = 0
VarBounds = (0, 100)

Engine = 'cbc'
TimeLimit = 60   # seconds