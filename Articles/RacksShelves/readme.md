## Warehouse space for free
In this article series, we look at improving the efficiency of a pallet warehouse (also known as a unit-load warehouse), where all items are stored on standard-size pallets.

Along the way, we:

- Formulate a non-linear model of the situation.
- Compare several solvers, to see how they perform.
- Linearize our model to, hopefully, make it easier to solve.
- Disaggregate our model to make some variables exogenous, then iterate over an enumeration of the exogenous variables.
- Demonstrate use of Pyomo's last() and next() functions, which enable us to work with elements of ordered sets.
- Turn off a constraint using Pyomo's deactivate() function.

Importantly, we show that there's a surprising amount of extra storage space available for free, or minimal cost, just by redesigning the warehouse's racks and shelves.

The model is built in Python using Pyomo.

Blog article: https://www.solvermax.com/blog/warehouse-space-for-free-non-linear-model
