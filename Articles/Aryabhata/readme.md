## Optimal rational approximation using SciPy
In this article we solve a non-linear curve fitting problem using the SciPy library. SciPy is especially well-suiting to solving this type of problem, as it includes a variety of functions for fitting and optimizing non-linear functions.

Along the way, we illustrate how to use SciPy's curve_fit and minimize functions for this type of task. In addition, we look at some good practices to apply when solving this type of problem, including:
- Using different criteria for defining the best fit, such as sum of squared differences and largest absolute error.
- Examining use of the full_output option when using the curve_fit function, to get more information about the result.
- Examining the success and message values of the minimize function result to ensure that the solver converges correctly.
- Trying a variety of minimize solution methods to see which one works best in our specific situation.
- Fine-tuning the solution by changing the convergence tolerance.

Blog article: [Optimal rational approximation using SciPy](https://www.solvermax.com/blog/optimal-rational-approximation-using-scipy)
