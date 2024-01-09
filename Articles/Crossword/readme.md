## Crossword MILP
Completing crossword puzzles is a popular pastime. There are many puzzle variations, ranging from simple to fiendishly difficult.

The process of creating a crossword puzzle – known as "compiling" – is difficult. Compiling a crossword can be thought of as a type of search problem, where we need to find a set of words that fits the rules for filling a specific crossword grid. Unsurprisingly, many crossword compilers use software to help them find a suitable set of words.

We build and test two Mixed Integer Linear Program (MILP) models to compile crosswords.

In this series of articles, we discuss:

- Representing a word puzzle in mathematical terms, enabling us to formulate the crossword compilation problem as a MILP model.
- Techniques for fine-tuning the model-building process in Pyomo, to make a model smaller and faster, including omitting constraint terms, skipping constraints, and fixing variable values.

Blog article: https://www.solvermax.com/blog/crossword-milp-model-1
