## Vaccination plan for Hong Kong
In this article we replicate an academic paper's model formulation of a [COVID-19 vaccination plan for Hong Kong](https://researchinfotext.com/ropen/attachments/articles/pdfs/259006COVID20-5050.pdf).

The model represents the supply of, and demand for, vaccine doses as a transportation problem, with doses "transported" from month-to-month given a storage cost rate. The objective is to minimize the total storage cost, while matching monthly supply and demand.

The paper's author solves the model using Excel and Solver. We do the same, though we also use OpenSolver – to see how it behaves differently. To incentivize the model to produce an intuitively better solution, we extend the model to include an escalating cost over time.

Blog article: [Vaccination plan for Hong Kong](https://www.solvermax.com/blog/vaccination-plan-for-hong-kong)
