## Schedule staff with enumerated shifts
A common application of optimization modelling is the scheduling of staff to meet demand. Scheduling problems can be difficult to solve, as there are often very specific requirements that need to be met, including staff availability, working hours, break times, etc.

One approach for formulating scheduling problems is to enumerate all possible shift patterns and then decide how many of each shift pattern to use so that we meet the various constraints at least cost. Enumeration of all possible shift patterns is often not as difficult as it may sound. We used a similar technique in the model Green manufacturing via cutting patterns. In that situation, there were potentially thousands of possible patterns, requiring an automated process to generate them all. In the staff scheduling situation there is usually a much smaller number of possible patterns, so manual enumeration is often possible.

In these blog articles we implement a staff scheduling model using two tools:
- Excel, using the CBC solver via OpenSolver.
- Python, using the CBC solver via Pyomo.

Blog article: https://www.solvermax.com/blog/schedule-staff-with-enumerated-shifts-opensolver
