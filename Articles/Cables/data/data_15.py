# Machine names must be consecutive letters, starting with A
A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z = list(range(26))   # Machine names

cable_struct = [[A, B, 2],   # machine_from, machine_to, cables
                [A, C, 1],
                [A, F, 3],
                [A, H, 1],
                [B, D, 1],
                [B, F, 2],
                [B, G, 1],
                [C, B, 2],
                [C, H, 1],
                [D, E, 1],
                [D, F, 2],
                [E, B, 1],
                [F, G, 1],
                [F, H, 2],
                [G, A, 1],
                [H, B, 1],
                [I, G, 2],                    
                [J, E, 1],
                [K, H, 2],
                [L, C, 2],
                [M, F, 3],
                [M, I, 2],
                [N, B, 1],
                [N, D, 3],
                [O, J, 1]
               ]