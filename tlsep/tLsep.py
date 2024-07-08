import time
import argparse
import subprocess
from copy import deepcopy
import re

import parse
import observationTable
import era
import event
import expression
import symbolicword
import stats
from config import tchecker_path

def extract_details(edge: str) -> list:
    ''' this function parses one edge's description inside a certificate
        returned by TChecker
        it expects the edge to be of the following form:
        'src -> tgt [delay="", guard="...", reset="...", src_invariant="", tgt_invariant="", vedge="<...>"]\n'

        arguments:
            edge    : a string describing an edge
        
        returns:
            a list containing [src, tgt, guard, reset]
    '''
    parsed_edge = re.match(r'^[ ]+([0-9]+) -> ([0-9]+) \[delay=".*?"\, guard="(.*?)", reset="(.*?)", src_invariant=".*?", tgt_invariant=".*", vedge="<.*?>"', edge)
    assert parsed_edge is not None
    
    src = parsed_edge.group(1)
    tgt = parsed_edge.group(2)
    
    guard = parsed_edge.group(3).replace(' ','')
    reset = parsed_edge.group(4)

    return [src, tgt, guard, reset]

def extract_cex(path: str, eventlist: list) -> symbolicword.SymWord:
    '''this function extracts a counter-example 
       from the certificate returned by TChecker
       NOTE: this function expects that only the digraph portion of the 
             output is passed as the argument and 
             not the whole output of TChecker

        Arguments: 
            path        = the certificate (a DOT file) returned by TChecker    
            eventlist   = a list of events 
        Returns:
            a symbolic word representing the path
    '''
    assert path[0][:7] == 'digraph'
    
    # find the first line that describes an edge 
    pos = 0
    for i in range(len(path)):
        if 'initial="true"' in path[i]:
            initial_state = re.search(r'[ ]+([0-9]+)', path[i]).group(1)
            
        if '->' in path[i]:
            pos = i
            break
        
    if len(path[1:-1]) == 1:
        # this is the case when the initial state itself is accepting
        return symbolicword.SymWord([symbolicword.SymEvent('EPSILON')])
    assert '->' not in path[pos-1] and '->' in path[pos]

    edges = dict()
    for l in path[pos:-1]:
        # one line represents a transition in the zone graph
        src, tgt, actual_guard, reset = extract_details(l)
        
        event_name = re.search(r'vedge="<.*@(.*)>"', l).group(1)
        event = None
        for existing_event in eventlist:
            if existing_event.name == event_name:
                event = existing_event
                break
        
        g = expression.typecheck(actual_guard)
        
        assert src not in edges.keys()
        edges[src] = (tgt, (symbolicword.SymEvent.constructUsingEventGuard(event, g)))
        
    path_word = symbolicword.SymWord([])
    curr_state = str(initial_state)
    while curr_state in edges.keys():
        path_word.symbolic_word.append(edges[curr_state][1])
        curr_state = edges[curr_state][0]
    return path_word

def is_product_empty(a: era.ERA, b: era.ERA):
    ''' given two automata, check if a X b is empty 
        this function, computes the product automaton a X b
        then, it calls TChecker on this product automaton
        to check if the product automaton is empty or not.
        If it is non-empty then TChecker returns a path that leads to 
        one of the final states in the product automaton

        arguments:
            a, b    : two ERAs
        
        returns:
            a file containing the output received from TChecker 
    '''
    product: era.ERA = a * b
    input_to_tchecker = './tmp/inputfile.txt'
    product.write_era_to_file(input_to_tchecker)

    output_of_tchecker = './tmp/outputfile.txt'
    with open(f'{output_of_tchecker}', 'w') as outfileobj:
        # subprocess.call(["./tchecker-lib/install/bin/tck-reach","-a","covreach","-C","symbolic","-l","accepting",input_to_tchecker])
        subprocess.call([tchecker_path,"-a","covreach","-C","concrete","-l","accepting",input_to_tchecker], stdout=outfileobj, stderr=outfileobj)
    with open(f'{output_of_tchecker}', 'r') as outfileobj:
        return outfileobj.readlines()

def is_product_empty_noprod(a: era.ERA, b: era.ERA):
    ''' given two ERA a and b, check if a * b is empty 
        this function, avoids computing the product automaton a * b
        it instead checks emptiness by considering a and b as 
        two automata in a network
        If it is non-empty then TChecker returns a path that leads to 
        one of the final states in the product automaton

        arguments:
            a, b    : two ERA
        
        returns:
            a file containing the output received from TChecker 
    '''
    input_to_tchecker = './tmp/inputfile.txt'
    # print(f'checking emptiness of the product of the following automata: {a} {b}')
    a_str = a.description_for_tchecker('P1')
    b_str = b.description_for_tchecker('P2')
    with open(input_to_tchecker, 'w') as infile:
        infile.write('system:my_sys{}\n\n')

        # define events
        assert a.events == b.events
        for e in a.events:
            infile.write(f'event:{e.name}\n')
        
        # define clocks
        assert a.active_clocks == b.active_clocks
        for e in a.active_clocks:
            infile.write(f'clock:1:{e.name}\n')

        infile.write(a_str)
        infile.write('\n')
        infile.write(b_str)
        infile.write('\n')
        
        # write the synchronizations
        for c in a.events:
            infile.write(f'sync:P1@{c}:P2@{c}\n')

    output_of_tchecker = './tmp/outputfile.txt'
    with open(f'{output_of_tchecker}', 'w') as outfileobj:
        # subprocess.call(["./tchecker-lib/install/bin/tck-reach","-a","covreach","-C","symbolic","-l","accepting",input_to_tchecker])
        subprocess.call([tchecker_path,"-a","covreach","-C","concrete","-l","P1accepting,P2accepting",input_to_tchecker], stdout=outfileobj, stderr=outfileobj)
    with open(f'{output_of_tchecker}', 'r') as outfileobj:
        return outfileobj.readlines()

def check_inclusion(a1: era.ERA, a2: era.ERA) -> symbolicword.SymWord:
    stats.IQ += 1

    a2_c = deepcopy(a2)
    a2_c.complement()
    output_of_tchecker = is_product_empty(a1, a2_c)

    index = 0
    if (len(output_of_tchecker))<2:
        return
    for l in output_of_tchecker:
        if len(l) < 3:
            return
        if 'REACHABLE' in l:
            if 'false' in l:
                return
        if 'digraph' in l:
            index = output_of_tchecker.index(l)
            break
    cex = extract_cex(output_of_tchecker[index:], a1.events)
    return cex

def is_equal(a: era.ERA, b: era.ERA) -> bool:
    if ((check_inclusion(a,b) == None) and (check_inclusion(b,a) == None)):
        return True
    return False

def check_completeness(automaton: era.ERA, sul: era.ERA):
    cex = check_inclusion(automaton, sul)
    if cex is not None:
        return (cex, False)
    
    automaton_rej = deepcopy(automaton)
    automaton_rej.make_dc_states_accepting()
    cex = check_inclusion(sul, automaton_rej)
    if cex is not None:
        return (cex, True)

    return (None, True)

def find_set_max_card(s: set):
    ''' argument: set of sets
        return: the set with max cardinality
        if there are more than one, choose non-deterministically
    '''
    index = 0
    
    # find the set with max length
    for i in range(1,len(s)):
        if (len(s[i]) > len(s[index])):
            index = i
    return s[index]

def invert_dict(d):
    return {v: k for k, v in d.items()}

def compute_minimal_dera(a: era.ERA):
    max_compatible_sets = a.find_maximal_compatible_sets()
    max_init_sets = [s for s in max_compatible_sets if 0 in s]
    init_state = find_set_max_card(max_init_sets)   # the first element among max sets containing 0
  
    #set of accepting states
    accepting_sets = [s for s in max_compatible_sets if any(a.states[i].accepting for i in s)]

    new_era = era.ERA(0)
    new_era.events = a.events[:]
    new_era.active_clocks = a.active_clocks[:]

    # create a dict: states_dict[index of state] = index of the corr. set in max_compatible_sets
    states_dict = dict()
    # find index of init_state
    q_in = new_era.add_state()
    new_era.make_initial(q_in.index())
    states_dict[q_in.index()] = max_compatible_sets.index(init_state)

    # for a forward analysis, keep a stack of state indices
    stack = []
    stack.append(q_in.index())

    # pop the first element from the stack and create a new state
    while len(stack) != 0:
        current_index = stack.pop(0)
        current_state = new_era.states[current_index]

        # check if the new state is accepting
        if max_compatible_sets[states_dict[current_index]] in accepting_sets:
            new_era.make_final(current_index)

        # add transitions from the new state
        for letter in a.transitions_on_letters_from_state.keys():
            e = event.Event(letter[0])
            g = expression.typecheck(letter[1])

            out_set_on_letter_from_i = set()

            for index in max_compatible_sets[states_dict[current_index]]:
                if index in a.transitions_on_letters_from_state[letter].keys():
                    out_set_on_letter_from_i.update(a.transitions_on_letters_from_state[letter][index])
            
            # out_set_on_letter_from_i is the basically delta(current_max_set, (e,g))
            if len(out_set_on_letter_from_i)!=0:
                
                # find the maximal set that contains out_set_on_letter_from_i : there exists at least one
                out_maximal_sets = [s for s in max_compatible_sets if out_set_on_letter_from_i.issubset(s)]
                next_set = find_set_max_card(out_maximal_sets)

                # find corresponding state for next_set
                next_set_index = max_compatible_sets.index(next_set)
                inverted_states_dict = invert_dict(states_dict)
                out_index = inverted_states_dict.get(next_set_index)

                if out_index is None:   # i.e., no corresponding state yet, so create new and add it to the stack
                    q_new = new_era.add_state()
                    states_dict[q_new.index()] = next_set_index
                    stack.append(q_new.index())
                    out_index = q_new.index()
                

                # finally, add the transition
                tgt_state = new_era.states[out_index]
                new_era.nd_add_transition(current_state, e, g, tgt_state)

    return new_era
    
def run_tLsep(sul: era.ERA, m: int) -> era.ERA:
    ''' this function implements the algorithm tLsep
        
        arguments:
            sul      : an ERA that is to be learnt
            m        : maximum constant present in the guards

        returns:
            an ERA having the same language as sul
    '''
    observation_table = observationTable.ObservationTable(sul, m)

    sul_c = deepcopy(sul)
   
    observation_table.add_S_dot_sigma()
    
    while True:
        while True:
            stats.EQ+=1
            observation_table.make_close_and_consistent()

            candidate_automaton, states_dict = observation_table.generate_3era()

            # completeness check
            cex, accepted_by_sul = check_completeness(candidate_automaton, sul_c)
            if cex is None:
                break

            observation_table.add_cex(cex, candidate_automaton, accepted_by_sul, states_dict, add_all_prefixes=False)

        stats.EQ+=1

        minimal_consistent_dera = compute_minimal_dera(candidate_automaton)
        
        # soundness check
        cex = check_inclusion(sul_c, minimal_consistent_dera)
        if cex is not None:
            accepted_by_sul = True

        if cex is None:
            cex = check_inclusion(minimal_consistent_dera, sul_c)
            if cex is not None:
                accepted_by_sul = False

            if cex is None:
                minimal_consistent_dera.remove_sinks()
                return minimal_consistent_dera


        observation_table.add_cex(cex, candidate_automaton, accepted_by_sul, states_dict, add_all_prefixes=True)



if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description="run tLsep algorithm to learn an ERA")
    argparser.add_argument('--sul', dest='sul', type=str,
                                    help="filename describing the sul", 
                                    required=True, metavar="<str>")
    argparser.add_argument('--m', dest='m', type=int,
                                  help="maximum constant appearing in guards", 
                                  required=True, metavar="<int>")
    args = argparser.parse_args()

    m = args.m
    
    start = time.time()

    # read the sul from file
    sul = parse.build_era_from_file(args.sul)

    # run tLsep
    automaton = run_tLsep(sul, m)

    print(automaton)

    print(f'total time taken: {time.time() - start}')
    print(f'# membership queries {stats.MQ}')
    print(f'# membership queries with cache {stats.MQc}')
    print(f'# inclusion queries {stats.IQ}')
    print(f'# equivalence queries {stats.EQ}')
    print(f'# times all_prefixes were added {stats.all_prefixes}')
    print(f'# times Rivest-Schapire was used {stats.rs_calls}')