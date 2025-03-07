# Network data for potato LMP model

def case_name():  # Return name of this case
    return 'Current'
    
def get_node_data():  # Data for each node
    return {
        # node_id: (max_supply, demand, supply_cost, [connected_node_ids])
        1: (100000, 0, 0.80, [2, 3]),
        2: (60000, 40000, 1.05, [1, 4, 5]),
        3: (25000, 30000, 0.90, [1, 4]),
        4: (0, 20000, 1.10, [2, 3, 5, 6]),
        5: (0, 25000, 1.12, [2, 6]),
        6: (0, 50000, 1.15, [4, 5])
    }

def get_connection_data():  # Data for each edge
    return {
        # (from, to): (capacity, distance, cost, fixed loss, variable loss)
        (1, 2): (80000, 150, 0.0010, 0.011*0, 0.00030),
        (1, 3): (40000, 200, 0.0015, 0.010*0, 0.00035),
        (2, 4): (50000,  95, 0.0024, 0.020*0, 0.00032),
        (2, 5): (20000, 100, 0.0012, 0.014*0, 0.00015),
        (3, 4): (90000, 120, 0.0012, 0.010*0, 0.00020),
        (4, 5): (20000,  50, 0.0025, 0.010*0, 0.00022),
        (4, 6): (50000,  75, 0.0008, 0.012*0, 0.00018),
        (5, 6): (60000,  60, 0.0011, 0.010*0, 0.00031)
    }
    
def get_node_positions():  # Position of each node
    return {
        1: (0.2, 0.8),
        2: (0.5, 0.8),
        3: (0.2, 0.5),
        4: (0.5, 0.5),
        5: (0.8, 0.5),
        6: (0.8, 0.2)
    }

def get_plot_data():
    node_label_offsets = {  # Position labels for each node
        1: (-0.13, +0.00),
        2: (+0.05, +0.00),
        3: (-0.13, +0.00),
        4: (-0.11, -0.06),
        5: (+0.04, +0.00),
        6: (+0.04, +0.00)
    }
    
    edge_label_offsets = {  # Position labels for each edge. State both directions, in case want to be non-symmetric
        (1, 2): (-0.05, -0.05),
        (2, 1): (-0.05, -0.05),
        (1, 3): (-0.10, +0.00),
        (3, 1): (-0.10, +0.00),
        (2, 4): (-0.10, +0.00),
        (4, 2): (-0.10, +0.00),
        (3, 4): (-0.05, +0.05),
        (4, 3): (-0.05, +0.05),
        (2, 5): (+0.01, +0.04),
        (5, 2): (+0.01, +0.04),
        (4, 5): (-0.05, +0.05),
        (5, 4): (-0.05, +0.05),
        (4, 6): (+0.01, +0.04),
        (6, 4): (+0.01, +0.04),
        (5, 6): (+0.02, +0.00),
        (6, 5): (+0.02, +0.00),
        }
    return node_label_offsets, edge_label_offsets
