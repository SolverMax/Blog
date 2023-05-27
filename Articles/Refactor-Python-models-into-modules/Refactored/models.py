# Model functions

def defineModel1():   # Base case model, with additive Professor and Student preference weights
    model = ConcreteModel()
    model.i = RangeSet(Nprof)
    model.j = RangeSet(Nstudent)
    
    model.Coef = Param(model.i, model.j, initialize = 0, mutable = True)
    for (i,j) in P:
        model.Coef[i, j] = P[i, j] + Q[i, j]
    
    model.U = Var(model.i, model.j, initialize = 0, within = Binary)
    
    def rule_c1(model, i):
        return sum(model.U[i, j] for j in model.j) <= cap[i]
    model.C1 = Constraint(model.i, rule = rule_c1)
    
    def rule_c2(model, j):
        return sum(model.U[i, j] for i in model.i) == 1
    model.C2 = Constraint(model.j, rule = rule_c2)

    def rule_of(model):
        return sum(model.Coef[i, j] * model.U[i, j] for j in model.j for i in model.i) 
    model.obj = Objective(rule = rule_of, sense = maximize)

    return model

def defineModel2(model):   # Change weights to be multiplicative
    for (i, j) in P:
        model.Coef[i, j] = P[i, j] * Q[i, j]
    return model

def defineModel3(modelInherit):   # Add constraints for minimum Professor and Student outcomes. Duplicates model, without changing existing model
    model = copy.deepcopy(modelInherit)
    model.ProfMinScore = Param(mutable = True, initialize = ProfMinScore)
    model.StudentMinScore = Param(mutable = True, initialize = StudentMinScore)
    
    def rule_minForProf(model, i):
        return sum(model.U[i, j] * P[i, j] for j in model.j) >= model.ProfMinScore * sum(model.U[i, j] for j in model.j)
    model.C_Prof_Min = Constraint(model.i, rule = rule_minForProf)
    
    def rule_minForStudent(model, j):
        return sum(model.U[i, j] * Q[i, j] for i in model.i) >= model.StudentMinScore
    model.C_Student_Min = Constraint(model.j, rule = rule_minForStudent)

    return model
    
def defineModel4(modelInherit):   # Generate efficient frontier by adding to existing model. Duplicates model, without changing existing model
    model = copy.deepcopy(modelInherit)
    model.limit = Param(initialize = 0, mutable = True)
    model.obj_prof = Var(initialize = 0, within = NonNegativeReals)
    model.obj_students = Var(initialize = 0, within = NonNegativeReals)
    
    def rule_c3(model):
        return sum(Q[i, j] * model.U[i, j] for i in model.i for j in model.j) == model.obj_students
    model.C3 = Constraint(rule = rule_c3)
    
    def rule_c4(model):
        return sum(P[i, j] * model.U[i, j] for i in model.i for j in model.j) == model.obj_prof
    model.C4 = Constraint(rule = rule_c4)
    
    def rule_c5(model):
        return model.obj_students >= model.limit
    model.C5 = Constraint(rule = rule_c5)
    
    return model

def defineModel5(modelInherit):   # Change minimum Professor and Student outcomes. Duplicate model, without changing existing model
    model = copy.deepcopy(modelInherit)
    model.StudentMinScore = StudentMinScore
    model.ProfMinScore = ProfMinScore
    
    return model