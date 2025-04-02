## Pivot irrigators in a 100 acre field
In this article, we explore a model for optimizing the layout of centre-pivot irrigation machines in a field. Our goal is to see if replacement of the existing worn-out machines would make purchase of a field a viable investment.

Arranging pivot irrigators in a field is a type of circle packing problem, with a non-linear objective and non-linear constraints. Worse still, the model is non-convex. These characteristics make our optimization problem both difficult and interesting.

To solve our model, we try several free and commerical solvers. All fail to find good solutions, except in trivial cases. So we try another solver, MINLP-BB via NEOS Server, that finds locally optimal solutions with no guarantee of global optimality. But by using a multi-start technique, we improve our chances of finding a good, perhaps optimal, solution. Is that solution good enough to justify making an investment?

Note that the model uses the NEOS Server service. You will need to change the EMAIL constant to be your email address.

Blog article: [Pivot irrigators in a 100 acre field](https://www.solvermax.com/blog/pivot-irrigators-in-a-100-acre-field)
