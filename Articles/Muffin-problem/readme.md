## The muffin problem
In this article, we solve 'The Muffin Problem' which is a recreational maths puzzle that is simple to state but hard to solve in general.

The goal of the muffin problem is to divide a number of muffins equally between a number of students, maximizing the size of the smallest piece that any student receives. Some cases are trivial, while some others are easy. But once we have more than a few muffins and/or students, this becomes a difficult problem to solve.

We use a Mixed Integer Linear Program to solve the problem. Along the way we play with some parallel computing to substantially reduce the run time, and throw in some symmetry-breaking constraints and objective function bounds to help the solver.

Blog article: [The muffin problem: A slice of recreational maths](https://www.solvermax.com/blog/the-muffin-problem-a-slice-of-recreational-maths)
