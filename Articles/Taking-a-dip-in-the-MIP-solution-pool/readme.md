## Taking a dip in the MIP solution pool
We're frequently asked questions like: "How many other optimal solutions exist?" and "How do I find those solutions?". Often these questions are prompted by our mentioning that most models have alternative optima – that is, optimal solutions with the same objective function value, but different variable values.

Although a model may have a unique optimal solution, models with integer/binary variables typically have multiple optimal solutions, and continuous linear models may have an infinite number of alternative optimal solutions. The likely existence of multiple alternative optima is why we usually say "an optimal solution", rather than saying "the optimal solution".

Sometimes people also ask, "How do I find solutions that are almost optimal?". This question typically indicates that the decision maker may accept a sub-optimal solution (or an alternative optimal solution) that is "better" according to some criteria that aren't captured by the model design. Of course, we should look at incorporating the unspecified criteria within the model, but sometimes that is difficult or even impossible. In any case, exploring the solution space around the optimal solution is an important part of the modelling process.

This article describes methods for finding alternative optima and solutions that are almost optimal. Specifically, we explore the CPLEX "solution pool" feature, which NEOS Server has recently made available through their online portal.

Blog article: [Taking a dip in the MIP solution pool](https://www.solvermax.com/blog/taking-a-dip-in-the-mip-solution-pool)
