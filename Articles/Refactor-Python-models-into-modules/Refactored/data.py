# Data functions

def defineData():   # Create random data for models
    random.seed(4)   # Define a seed, so random numbers are the same in each run
    P, Q, cap = {}, {}, {}
    a = [j for j in range(1, 1 + Nstudent)]   # List 1..j of Students
    b = [i for i in range(1, 1 + Nprof)]   # List 1..i of Professors
    for i in range(1, 1 + Nprof):
        cap[i] = random.randint(ProfMinCapacity, ProfMaxCapacity)   # Professor capacity for advising students
        random.shuffle(a)
        for j in range(1, 1 + Nstudent):
            P[i, j] = a[j - 1]   # Preference of Professor i for Student j
    for j in range(1, 1 + Nstudent):
        random.shuffle(b)
        for i in range(1, 1 + Nprof):
            Q[i, j] = b[i - 1]   # Preference of Student j for Professor i
    return a, b, P, Q, cap