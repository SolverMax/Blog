## Logic constraints
When formulating a model, we often have a situation described in terms of logic conditions where something implies something else. For example:
- If this happens, then we must do that.
- If this and that happen, then we can't do some other thing.
- We can do some or all of these things, but only if that other thing happens.

However, mathematical programming models cannot represent logic conditions directly. Therefore, we need to translate the conditions, known as "implications", into a set of constraints that represent the logic.

In Part 1 we describe a technique for converting a logical implication into an equivalent set of constraints. Along the way, we'll dabble in applying some formal logic notation, define rules for manipulating formal logical implications, have a brief look at Conjunctive Normal Form (CNF), and learn how to convert CNF into constraints.

Part 2 describes an alternative representation of this technique, specifically designed to improve the proficiency of students learning to formulate models.

Blog articles:

[Logic conditions as constraints - Part 1](https://www.solvermax.com/blog/logic-conditions-as-constraints-part-1)

[Logic conditions as constraints - Part 2](https://www.solvermax.com/blog/logic-conditions-as-constraints-part-2)
