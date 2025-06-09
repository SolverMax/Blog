# Jury simulation model
# www.solvermax.com

import random
import matplotlib.pyplot as plt
import numpy as np
import logging
import sys

MODE = 2  # Select run type. See definitions in setup_simulation

# Common constants
JURY_SIZE = 12  # People required on a jury
TRIALS_MEAN = 3  # Average number of trials per week (Poisson distribution)
COURTROOMS = 9  # Max trials per week
CHALLENGE_RATE_POOL = 25  # % pool candidates challenged before empanelling
CHALLENGE_MAX_POOL = 8  # Maximum number of pool candidates that can challenged
CHALLENGE_MAX_MIXED = 2  # Maximum number of assigned candidates that can be challenged (in court, after initial assignment)
EXCUSE_EMPANELLING = 10  # % of people who ask a Judge to be excused during the empanelling process
REMOVE_DISTN = 'binomial'  # Choice of probability distribution for removing candidates, either 'normal' or other (i.e. binomial)

# Pool constants
EXCUSE_MEAN_POOL = 25  # % pool candidates excused
EXCUSE_STDEV_POOL = 6  # Standard deviation for pool excuse rate
NOSHOW_MEAN_POOL = 20  # % pool candidates who no show
NOSHOW_STDEV_POOL = 5  # Standard deviation for pool no show rate

# Assignment constants
EXCUSE_MEAN_ASSIGN = 25  # % assigned candidates excused
EXCUSE_STDEV_ASSIGN = 6  # Standard deviation for assigned excuse rate
NOSHOW_MEAN_ASSIGN = 20  # % assigned candidates who no show
NOSHOW_STDEV_ASSIGN = 5  # Standard deviation for assigned no show rate

class Stats:  # Collate statistics during run
    def __init__(self):
        self.overall = {"total_trials": 0, "successful": 0, "failed": 0, "success_detail": {}, "fail_detail": {}}
        self.assign = {"initial": 0, "excused": 0, "available": 0, "noshow": 0, "show": 0, "empanelled": 0}
        self.pool = {"initial": 0, "excused": 0, "available": 0, "noshow": 0, "show": 0, "empanelled": 0}

def setup_simulation(mode):  # Define constants for current and proposed
    if mode not in [1, 2, 3]:
        print('Error: Invalid mode')
        sys.exit(1)

    POOL_PER_TRIAL = 54  # Current number of people summoned per trial
    MIN_POOL = 0  # Current minimum size of the juror pool, before being excused or no show
    ASSIGNED_PER_TRIAL = 0  # Current number of jurors assigned per trial

    config = {
        1: {  # Debug mode. Run only 1 week (or maybe a few weeks)
            "NUM_WEEKS": 1,
            "LOG_LEVEL": logging.INFO,
            "POOL_PER_TRIAL_SCENARIOS": [54],
            "MIN_POOL_SCENARIOS": [0],
            "ASSIGNED_PER_TRIAL_SCENARIOS": [0],
            "DETAILED_STATS": True
        },
        2: {  # Run a specific pair of scenarios (Current and Proposed), with detailed statistics
            "NUM_WEEKS": 1000000,
            "LOG_LEVEL": logging.WARNING,
            "POOL_PER_TRIAL_SCENARIOS": [7],
            "MIN_POOL_SCENARIOS": [21],
            "ASSIGNED_PER_TRIAL_SCENARIOS": [23],
            "DETAILED_STATS": True
        },
        3: {  # Run a range of parameters, without debug information and printing summary statistics only
            "NUM_WEEKS": 100000,
            "LOG_LEVEL": logging.WARNING,
            "POOL_PER_TRIAL_SCENARIOS": range(0,21),
            "MIN_POOL_SCENARIOS": range(0,21),
            "ASSIGNED_PER_TRIAL_SCENARIOS": [14],
            "DETAILED_STATS": False
        }
    }
    settings = config[mode]
    NUM_WEEKS = settings["NUM_WEEKS"]
    logging.basicConfig(level = settings["LOG_LEVEL"])
    POOL_PER_TRIAL_SCENARIOS = settings["POOL_PER_TRIAL_SCENARIOS"]
    MIN_POOL_SCENARIOS = settings["MIN_POOL_SCENARIOS"]
    ASSIGNED_PER_TRIAL_SCENARIOS = settings["ASSIGNED_PER_TRIAL_SCENARIOS"]
    DETAILED_STATS = settings["DETAILED_STATS"]
    return POOL_PER_TRIAL, MIN_POOL, ASSIGNED_PER_TRIAL, NUM_WEEKS, POOL_PER_TRIAL_SCENARIOS, MIN_POOL_SCENARIOS, ASSIGNED_PER_TRIAL_SCENARIOS, DETAILED_STATS
    
def initialize_stats():
    return Stats()

def trials_sequence():  # Generate and store the sequence of trials
    np.random.seed(42)
    trial_sequences = [generate_trials_count() for _ in range(NUM_WEEKS)]
    return trial_sequences
    
def generate_trials_count():  # Generate the number of trials
# Not allowing for truncation, if TRIALS_MEAN = 3 then:
# Distribution of prob(n) = 15%, 22%, 22%, 17%, 10%, 5%, 2%, 1%, 0.3% for n = 1..9
# Distribution of number of trials = prob(n) * n = 5%, 15%, 22%, 22%, 17%, 10%, 5%, 2%, 1% for n = 1..9
    trials = min(COURTROOMS, np.random.poisson(TRIALS_MEAN))  # Truncated Poisson distribution. Use carefully if COURTROOMS is small relative to TRIALS_MEAN
    logging.info(f'Number of trials: {trials}')
    return trials

def create_jury_list(list_type, num_trials, min_create, per_trial, start_at):  # Create a jury list given parameters, ensuring a minimum number of jurors.
    num_pool = max(min_create, per_trial * num_trials)
    pool = list(range(start_at, start_at + num_pool))
    logging.info(f'{list_type} list ({len(pool)}): {pool}')
    return pool, num_pool

def empanel_jurors(assigned, pool):  # Create a jury
    jury = assigned[:JURY_SIZE]
    assigned_count = len(jury)
    challenge_rate = CHALLENGE_RATE_POOL
    challenge_max = CHALLENGE_MAX_POOL if assigned_count == 0 else CHALLENGE_MAX_MIXED
    num_challenged = 0
    while len(jury) < JURY_SIZE:  # If jury is not full, continue selecting from pool
        if not pool:  # No more people in pool, so fail
            return jury, False
        current = random.sample(pool, 1)
        pool = [c for c in pool if c not in current]  # Remove current person from this trial's pool, whether or not they are enpanelled
        if random.uniform(0, 1) <= EXCUSE_EMPANELLING / 100:  # Excuse people from pool, if they ask the Judge
            logging.info(f'Excused by Judge {current}')
            continue  # Don't add excused person to jury
        if num_challenged < challenge_max:  # Only allow challenge if less than max challenges previously
            if random.uniform(0, 1) <= challenge_rate / 100:  # Successful challenge
                num_challenged += 1
                logging.info(f'Challenged {current}')
                continue  # Don't add challenged person to jury
        jury.extend(current)  # Add person to jury if they weren't excused or challenged
    return jury, True

def remove_candidates(remove_type, candidates, mean_rate, stdev_rate):  # Remove candidates and return remaining candidates etc
    if mean_rate > 0:  # Remove some number of randomly selected candidates
        mean = len(candidates) * mean_rate / 100
        stdev = mean * (stdev_rate / mean_rate)
        if REMOVE_DISTN == 'normal':  # Probability distribution for removing candidates
            num_removed = int(round(np.random.normal(mean, stdev), 0))  # Normal distribution
            num_removed = max(0, min(num_removed, len(candidates)))
        else:
            num_removed = np.random.binomial(len(candidates), mean_rate / 100, 1)[0]  # Binomial distribution
        candidates_remove = random.sample(candidates, num_removed)
    else:
        candidates_remove = []
    available = [c for c in candidates if c not in candidates_remove]
    available_rate = len(available) / len(candidates) if len(candidates) else 0
    logging.info(f'{remove_type} candidates removed ({len(candidates_remove)}): {candidates_remove}')
    return available, available_rate, num_removed

def make_assigned(stats, num_trials):  # Generate assigned jurors for a given number of trials, then remove excused and no shows
    assigned_jurors = []
    for _ in range(num_trials):
        assign_initial, num_assigned = create_jury_list('Assigned', 1, 0, ASSIGNED_PER_TRIAL, stats.assign['initial'] + 1)
        assign_available, _, assign_excused = remove_candidates('Assigned excused', assign_initial, EXCUSE_MEAN_ASSIGN, EXCUSE_STDEV_ASSIGN)
        assign_show, _, num_assign_noshow = remove_candidates('Assigned no show', assign_available, NOSHOW_MEAN_ASSIGN, NOSHOW_STDEV_ASSIGN)
        assigned_jurors.append(assign_show)
        stats.assign['initial'] += num_assigned
        stats.assign['excused'] += assign_excused
        stats.assign['noshow'] += num_assign_noshow
        stats.assign['show'] += len(assign_show)
    return assigned_jurors
    
def make_pool(stats, num_trials):  # Generate pool jurors for a given number of trials, then remove excused and no shows
    pool_initial, num_pool = create_jury_list('Pool', num_trials, MIN_POOL, POOL_PER_TRIAL, stats.assign['initial'] + 1)
    pool_available, _, pool_excused = remove_candidates('Pool excused', pool_initial, EXCUSE_MEAN_POOL, EXCUSE_STDEV_POOL)
    pool_show, _, num_pool_noshow = remove_candidates('Pool no show', pool_available, NOSHOW_MEAN_POOL, NOSHOW_STDEV_POOL)
    stats.pool['initial'] += num_pool
    stats.pool['excused'] += pool_excused
    stats.pool['noshow'] += num_pool_noshow
    stats.pool['show'] += len(pool_show)  # Aggregate count, not list
    return pool_show

def perform_trials(stats, assigned_jurors, pool_show, num_trials):  # Perform empanelling of jurors for each trial this week
    all_juries = []
    fail_count = 0
    assigned_used = 0
    pool_used = 0
    for trial in range(num_trials):
        jury, success = empanel_jurors(assigned_jurors[trial], pool_show)
        logging.info(f'Jury ({len(jury)}) {jury} {"Success" if len(jury) == JURY_SIZE else "Fail"}')
        all_juries.append(sorted(jury))
        if success:
            pool_show = [c for c in pool_show if c not in jury]  # Remove people empanelled on a jury
            num_assigned = min(JURY_SIZE, len(assigned_jurors[trial]))
            assigned_used += num_assigned
            pool_used += JURY_SIZE - num_assigned
        else:
            fail_count += 1    
    stats.overall['successful'] += num_trials - fail_count
    stats.overall['failed'] += fail_count
    stats.assign['empanelled'] += assigned_used
    stats.pool['empanelled'] += pool_used
    stats.overall['success_detail'][num_trials] = stats.overall['success_detail'].get(num_trials, 0) + (num_trials - fail_count)
    stats.overall['fail_detail'][num_trials] = stats.overall['fail_detail'].get(num_trials, 0) + fail_count

def simulate_week(stats, week_number, trial_sequences):  # Simulate a week by generating trials, assigning jurors, managing pool show-ups, and updating statistics
    num_trials = trial_sequences[week_number]
    if num_trials >= 1:  # Ignore weeks where there are no trials
        stats.overall['total_trials'] += num_trials
        assigned_jurors = make_assigned(stats, num_trials)
        pool_show = make_pool(stats, num_trials)
        lengths = [len(i) for i in assigned_jurors]
        logging.info(f'Assigned jurors ({lengths} = {sum(lengths)}: {assigned_jurors}')
        logging.info(f'Pool show ({len(pool_show)}): {pool_show}')
        perform_trials(stats, assigned_jurors, pool_show, num_trials)

def simulate_jury_selection(trial_sequences):  # Iterate over all weeks
    stats = initialize_stats()
    for i in range(NUM_WEEKS):
        simulate_week(stats, i, trial_sequences)
    return stats

def header(design):  # Print output header
    if design == 1:
        print('Jury selection simulation: Current design')
        print('=========================================\n')
    else:
        print('\nJury selection simulation: Proposed design')
        print('==========================================\n')
    print(f'Pool per trial: {POOL_PER_TRIAL}, minimum pool: {MIN_POOL}, assigned per trial: {ASSIGNED_PER_TRIAL}')

def write_stats(stats):  # Write statistics accumulated during the run
    a_i, a_e, a_n, a_s, a_m = stats.assign['initial'], stats.assign['excused'], stats.assign['noshow'], stats.assign['show'], stats.assign['empanelled']
    p_i, p_e, p_n, p_s, p_m = stats.pool['initial'], stats.pool['excused'], stats.pool['noshow'], stats.pool['show'], stats.pool['empanelled']
    t_success_pct = (stats.overall['successful'] / stats.overall['total_trials']) if stats.overall['total_trials'] > 0 else 0
    t_fail_pct = (stats.overall['failed'] / stats.overall['total_trials']) if stats.overall['total_trials'] > 0 else 0
    trial_keys = stats.overall['success_detail'].keys() | stats.overall['fail_detail'].keys()
    min_trials = max(1, min(trial_keys, default=0))
    max_trials = max(trial_keys, default=0)
    em_a_pct = a_m / a_s if a_s > 0 else 0
    em_p_pct = p_m / p_s if p_s > 0 else 0
    ex_a_pct = (a_s - a_m) / a_s if a_s > 0 else 0
    ex_p_pct = (p_s - p_m) / p_s if p_s > 0 else 0
    em_pct_tot = (a_m + p_m) / (a_s + p_s) if (a_s + p_s) > 0 else 0
    ex_pct_tot = ((a_s + p_s) - (a_m + p_m)) / ((a_s + p_s)) if (a_s + p_s) > 0 else 0
    t_i, t_e, t_n, t_s, t_m, t_ex = a_i + p_i, a_e + p_e, a_n + p_n, a_s + p_s, a_m + p_m, (a_s + p_s) - (a_m + p_m)
    
    if DETAILED_STATS:
        if stats.overall['total_trials'] >= 1:
            print(f'Weeks: {NUM_WEEKS:,.0f}\n')
            print(f'Jurors         Initial       Excused       No show          Show             Empanelled                 Extra')
            print(f'-------------------------------------------------------------------------------------------------------------')
            print(f'Assigned   {a_i:>11,.0f}   {a_e:>11,.0f}   {a_n:>11,.0f}   {a_s:>11,.0f}   {a_m:>11,.0f} ({em_a_pct:>6.1%})  {a_s - a_m:>11,.0f} ({ex_a_pct:>6.1%})')
            print(f'Pool       {p_i:>11,.0f}   {p_e:>11,.0f}   {p_n:>11,.0f}   {p_s:>11,.0f}   {p_m:>11,.0f} ({em_p_pct:>6.1%})  {p_s - p_m:>11,.0f} ({ex_p_pct:>6.1%})')
            print(f'-------------------------------------------------------------------------------------------------------------')
            print(f'Total      {t_i:>11,.0f}   {t_e:>11,.0f}   {t_n:>11,.0f}   {t_s:>11,.0f}   {t_m:>11,.0f} ({em_pct_tot:>6.1%})  {t_ex:>11,.0f} ({ex_pct_tot:>6.1%})')
            print(f'\nTrials                  Success                    Failure                  Total')
            print(f'---------------------------------------------------------------------------------')
            t_s_t, t_f_t, t_t_t = stats.overall['successful'], stats.overall['failed'], stats.overall['total_trials']
            total_pct = t_t_t/(t_s_t + t_f_t) if (t_s_t + t_f_t) > 0 else 0
            for t in range(min_trials, max_trials + 1):
                successes = stats.overall['success_detail'].get(t, 0)
                fails = stats.overall['fail_detail'].get(t, 0)
                total_trials = successes + fails
                success_pct = successes / total_trials if total_trials > 0 else 0
                failure_pct = fails / total_trials if total_trials > 0 else 0
                row_pct = total_trials/t_t_t if t_t_t > 0 else 0
                print(f'{t:>6,.0f} {successes:>11,.0f} ({success_pct:>10.5%})   {fails:>11,.0f} ({failure_pct:>10.5%})   {total_trials:>11,.0f} ({row_pct:>6.1%})')
            print(f'---------------------------------------------------------------------------------')
            print(f'Total   {t_s_t:>10,.0f} ({t_success_pct:>10.5%})   {t_f_t:>11,.0f} ({t_fail_pct:>10.5%})   {t_t_t:>11,.0f} ({total_pct:>6.1%})')
        else:
            print('No trial data')
    else:
        print(f'{POOL_PER_TRIAL},{MIN_POOL},{ASSIGNED_PER_TRIAL},{(a_s+p_s)-(a_m+p_m)},{t_fail_pct:>8.5%}')

def main(phase, trial_sequences):
    if DETAILED_STATS:
        header(phase)
    stats = simulate_jury_selection(trial_sequences)
    write_stats(stats)

if __name__ == "__main__":
    POOL_PER_TRIAL, MIN_POOL, ASSIGNED_PER_TRIAL, NUM_WEEKS, POOL_PER_TRIAL_SCENARIOS, MIN_POOL_SCENARIOS, ASSIGNED_PER_TRIAL_SCENARIOS, DETAILED_STATS = setup_simulation(MODE)
    trial_sequences = trials_sequence()
#    main(1, trial_sequences)  # Current
    for POOL_PER_TRIAL in POOL_PER_TRIAL_SCENARIOS:
        for MIN_POOL in MIN_POOL_SCENARIOS:
            for ASSIGNED_PER_TRIAL in ASSIGNED_PER_TRIAL_SCENARIOS:
                main(2, trial_sequences)  # Proposed