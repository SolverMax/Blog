## Symmetry-less 1D bin packing
Recently we were working on a small one-dimensional bin packing model. The situation was simple, and we expected the model to be easy to solve. But there was just one problem: we couldn't find an optimal solution, even after letting the solver run overnight for 12 hours.

Initially, we were using the CBC solver. Since that didn't work, we tried CPLEX via NEOS, but we encountered the same problem – CPLEX couldn't find an optimal solution either.

So, we searched the Operations Research literature for an alternative formulation. We discovered a recently published academic paper that has a new, innovative formulation for one-dimensional bin packing (and potentially other types of packing situations).

This article describes the new formulation and our experience applying it to our simple, yet difficult to solve, model.

Blog article: [Symmetry-less 1D bin packing](https://www.solvermax.com/blog/symmetry-less-1d-bin-packing)
