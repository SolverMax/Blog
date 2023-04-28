## Price breaks in a linear programming model
Price breaks, or volume discounts, are common when buying products in bulk. That is, the marginal cost of additional products falls as volume increases. In a linear program, price breaks are tricky to model because the break points are non-linear discontinuities.

In a spreadsheet, a natural way to model price breaks is to use functions like IF, VLOOKUP, CHOOSE, MIN, and/or MAX. However, those functions are discontinuous, so we can't use the Simplex linear method in Solver. We also can't use the OpenSolver solvers at all when our model includes those functions. We could use Solver's GRG non-linear or Evolutionary methods, but they are not always reliable.

Fortunately, there is a way to express price breaks linearly, by using some binary variables, as described in our article [MIP formulations and linearizations](https://www.solvermax.com/blog/mip-formulations-and-linearizations/).

In this article, we describe an example of how to represent price breaks in a linear programming model.

The model is built in Excel and solved using either Solver or OpenSolver.

Blog article: [Price breaks in a linear programming model](https://www.solvermax.com/blog/price-breaks-in-a-linear-programming-model)
