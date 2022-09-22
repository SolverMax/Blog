## Production mix - Model 6, Pyomo
In this article we continue the Python Production mix series, using the Pyomo library.
Specifically, we build Model 6, which changes Model 5 to:
- Declare the model as a Pyomo pyo.AbstractModel, rather than as a pyo.ConcreteModel.
- Read the data from a dat file rather than a json file.
These changes show that, contrary to how abstract and concrete models are portrayed in most blogs, there is actually little difference between abstract and concrete Pyomo models.
Blog article: [Production mix - Model 6, Pyomo](https://www.solvermax.com/blog/production-mix-model-6-pyomo)
