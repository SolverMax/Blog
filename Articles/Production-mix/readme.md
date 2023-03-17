## Production mix model
In this series of articles we build the "Production mix" optimization model using various Python Pyomo libraries.

In total, we build eleven versions of the model – all of which return the same solution, but using different libraries, solvers, and Python programming techniques.

Our first six models are built using Pyomo, starting with a simple "concrete" model, progressing through a variety of increasingly sophisticated concrete models, ending with an "abstract" model. The range of Pyomo models illustrates some of the many techniques that can be used to build optimization models in Python, even when using the same library.

We then build the model in each of five other libraries: PuLP, OR Tools, Gekko, CVXPY, and SciPy.

In addition to using different libraries to build the models, some libraries have multiple solvers available. For each model, we'll choose an appropriate solver, depending on which solvers are available to the library we're using.

Our conclusions are summarized in the blog article: https://www.solvermax.com/blog/production-mix-conclusions
