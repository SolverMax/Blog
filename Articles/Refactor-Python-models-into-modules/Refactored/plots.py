# Plot functions

def plotPreferences():   # Professor and Student preferences matrices
    plt.figure(figsize = (16, 10))
    plt.subplot(1, 2, 1)
    for (i, j) in P:
        plt.scatter(i, j, marker = 's', c = 'k', s = 30, alpha = P[i, j] / Nstudent)

    plt.xticks(b, fontweight = 'bold')
    plt.yticks(a, fontweight = 'bold')
    plt.xlabel(' Professors ', fontweight = 'bold')
    plt.ylabel(' Students ', fontweight = 'bold')
    plt.title('Preference of Professors for each student', fontweight = 'bold')
    plt.grid(zorder = -1)

    plt.subplot(1, 2, 2)
    for (i, j) in Q:
        plt.scatter(i, j, marker = 's', c = 'navy', s = 30, alpha = Q[i, j] / Nprof)

    plt.xticks(b, fontweight = 'bold')
    plt.yticks(a, fontweight = 'bold')
    plt.xlabel('Professors', fontweight = 'bold')
    plt.ylabel('Students', fontweight = 'bold')
    plt.grid(zorder = -1)
    plt.title('Preference of Students for each professor', fontweight = 'bold')
    if WriteImages:
        plt.savefig('DataofPreferences' + '.jpg', format = 'jpg', dpi = 400)
    plt.show()

def plotCapacity():   # Professor capacities
    plt.figure(figsize = (14, 6))
    cap_prof = [cap[i] for i in range(1, 1 + Nprof)]
    plt.bar(b, cap_prof, width = 0.5, facecolor = 'pink')
    plt.xticks(b, fontweight = 'bold')
    plt.yticks(fontweight = 'bold')
    plt.xlabel('Professors', fontweight = 'bold')
    plt.ylabel('Max Number of Students', fontweight = 'bold')
    plt.title('Capacity of supervision for professor (i)', fontweight = 'bold')
    plt.grid()
    if WriteImages:
        plt.savefig('Profscapacity' + '.jpg', format = 'jpg', dpi = 400)
    plt.show()

def plotWheel(Filename, model):   # Assignment of Students to Professors
    plt.figure(figsize = (8, 8))
    R = 10 
    r = 20 
    profx = [R + R * cos(theta) for theta in np.linspace(0, 1.9 * np.pi, Nprof)]
    profy = [R + R * sin(theta) for theta in np.linspace(0, 1.9 * np.pi, Nprof)]
    Tprofx = [R + 1.2 * R * cos(theta) for theta in np.linspace(0, 1.9 * np.pi, Nprof)]
    Tprofy = [R + 1.2 * R * sin(theta) for theta in np.linspace(0, 1.9 * np.pi, Nprof)]
    studentx = [R + r * cos(theta) for theta in np.linspace(0, 1.9 * np.pi, Nstudent)]
    studenty = [R + r * sin(theta) for theta in np.linspace(0, 1.9 * np.pi, Nstudent)]
    Tstudentx = [R + 1.1 * r * cos(theta) for theta in np.linspace(0, 1.9 * np.pi, Nstudent)]
    Tstudenty = [R + 1.1 * r * sin(theta) for theta in np.linspace(0, 1.9 * np.pi, Nstudent)]

    plt.plot(studentx, studenty, lw = 3, c = 'k')
    plt.scatter(studentx, studenty, s = 100, c = 'k', zorder = 400)

    plt.plot(profx, profy)
    plt.scatter(profx, profy, s = 100, c = 'k', zorder = 200)

    for i in model.i:
        x0, y0 = Tprofx[i - 1], Tprofy[i - 1]
        plt.text(x0, y0, s = str(i), c = 'k', fontsize = 13, fontweight = 'bold')
        for j in model.j:
            if value(model.U[i, j]) > 0:
                x0, y0 = profx[i - 1], profy[i - 1]
                x1, y1 = studentx[j - 1], studenty[j - 1]
                LW = P[i, j] + Q[i, j]
                plt.plot([x0, x1], [y0, y1], lw = 2, alpha = LW / 60)
                x1, y1 = Tstudentx[j - 1] - 1, Tstudenty[j - 1] - 2
                plt.text(x1, y1 + 2, s = str(j), c = 'r', fontsize = 13, fontweight = 'bold')
    plt.axis('off')
    if WriteImages:
        plt.savefig(Filename + '.jpg', format = 'jpg', dpi = 400)
    plt.show()

def plotAvg(satisfaction, group, pltColor, title, ymax, filename):   # Satisfaction of participants
    people = [n for n in group]
    plt.figure(figsize = (14, 6))
    plt.subplot(2, 1, 2)
    plt.ylim(0, ymax)
    plt.bar(people, satisfaction, width = 0.5, facecolor = pltColor)
    plt.xticks(people, fontweight = 'bold')
    plt.yticks(fontweight = 'bold')
    plt.title(title, fontweight = 'bold')
    plt.grid()
    if WriteImages:
        plt.savefig(filename + '.jpg', format = 'jpg', dpi = 100)
    plt.show()

def plotFrontier(OF1, OF2):   # Pareto efficient frontier
    plt.figure(figsize = (8, 8))
    plt.scatter(OF1, OF2, s = 100, c = 'k')
    
    plt.xlabel('$OF_1$ (Students satisfaction)', fontweight = 'bold', fontsize = 12)
    plt.ylabel('$OF_2$ (Profs satisfaction)', fontweight = 'bold', fontsize = 12)
    plt.xticks(fontweight = 'bold', fontsize = 12)
    plt.yticks(fontweight = 'bold', fontsize = 12)
    plt.grid()
    if WriteImages:
        plt.savefig('Paretooptimalfront' + '.jpg', format = 'jpg', dpi = 400)
    plt.show()    