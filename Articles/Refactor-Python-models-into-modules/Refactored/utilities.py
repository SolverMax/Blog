# Utility functions

def printResult(results, model, modelName, modelNum):   # Print solver status, objective function value, and plots
    print(modelName)
    if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
        print('Feasible')
        print(f'OF = {value(model.obj):,.0f}')
        plotWheel(modelName, model)
        Prof_satisfaction, Student_satisfaction = calcSatisfaction(P, Q, model)
        plotAvg(Prof_satisfaction, model.i, 'navy', 'Model ' + modelNum + ': Average satisfaction of professors', Nstudent, 'AvgCase-' + modelNum + 'a')
        plotAvg(Student_satisfaction, model.j, 'green', 'Model ' + modelNum + ': Student satisfaction', Nprof, 'AvgCase-' + modelNum + 'b')        
    elif (results.solver.termination_condition == TerminationCondition.infeasible):
        print('**** Infeasible ****')
    else:
        print ('Solver Status:', results.solver.status)
    
def calcSatisfaction(P, Q, model):   # Calculate outcome satisfaction of each participant
    Prof_satisfaction = []
    Student_satisfaction = []
    pd.set_option('display.max_columns', None)
    ProfScore = pd.DataFrame()
    StudentScore = pd.DataFrame()
    
    pd.options.display.float_format = "{:,.2f}".format
    print('Professor Average Score')
    for i in model.i:
        a = [P[i, j] * value(model.U[i, j]) for j in model.j if value(model.U[i, j]) > 0]
        Score = np.mean(a)
        Prof_satisfaction.append(Score)
        ProfScore.loc['Score', i] = Score
    display(ProfScore)

    pd.options.display.float_format = "{:,.0f}".format
    print('Student Score')
    for j in model.j:
        b = [Q[i, j] * value(model.U[i, j]) for i in model.i]
        Score = np.sum(b)
        Student_satisfaction.append(Score)
        StudentScore.loc['Score', j] = Score
    columns = 30
    rows = Nstudent // columns 
    for r in range(0, rows + 1):
        first = r * columns
        last = first + columns
        display(StudentScore.iloc[: , first:last])

    return Prof_satisfaction, Student_satisfaction
    
def frontier(model):   # Calculate Pareto efficient frontier
    for (i, j) in P:
        model.Coef[i, j] =  P[i, j]   # Weights to maximize Professor preferences; to get corresponding Student objective
    results = opt.solve(model)
    OF1min = value(model.obj_students)
    OF2max = value(model.obj_prof)
    print('Frontier start')
    print(f'OF1_(student) = {OF1min:,.0f}')
    print(f'OF2_(prof) = {OF2max:,.0f}')

    for (i, j) in Q:
        model.Coef[i, j] =  Q[i, j]   # Weights to maximize Student preferences. May not maximize Professor preferences
    results = opt.solve(model)
    OF1max = value(model.obj_students)
    OF2min = value(model.obj_prof)
    print('\nFrontier end')
    print(f'OF1_(student) = {OF1max:,.0f}')
    print(f'OF2_(prof) = {OF2min:,.0f}')

    N = 30 
    report = {}
    
    for (i, j) in P:
        model.Coef[i, j] = P[i, j]   # Maximize the Professor preferences objective

    for counter in range(N):   # Step through Student preferences range and find corresponding maximum Professor preferences
        model.limit = (OF1max - OF1min) * counter / (N - 1) + OF1min
        results = opt.solve(model)
        report[counter, 'OF1'] = round(value(model.obj_students), 4)
        report[counter, 'OF2'] = round(value(model.obj_prof), 4)
    OF1 = [report[counter, 'OF1'] for counter in range(N)]
    OF2 = [report[counter, 'OF2'] for counter in range(N)]

    return OF1, OF2