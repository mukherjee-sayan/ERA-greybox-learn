import re

import era
import event
import expression

def build_era_from_file(infile: str) -> era.ERA:
    ''' read a file containing the description of a (D)ERA
        arguments:
            infile : file containing description of a (D)ERA 
                     in a specific syntax
            
        returs:
            an ERA object
    '''
    event_list = dict()     # dict of events present in the automaton
    active_clocks = []      # dict of active clocks that appear in guards
    states_list = []        # list of states to be created
    transitions_list = []   # list of transitions to be created

    # reading the file 
    with open(infile, 'r') as f:
        everything = f.readlines()
        
        for eachline in everything:
            values = eachline.strip().split(':') 
            
            if values[0] == 'event': # for lines starting with 'event'
                event_details = values[1].split('{')
                event_name = event_details[0].strip()
                active = True if 'active' in event_details[1] else False
                new_event = event.Event(event_name)
                event_list[event_name] = new_event
                if active:
                    active_clocks.append(new_event)
            
            elif values[0] == 'location': # for lines starting with 'location'
                # extract the name of the state as given in the file
                state_name = re.search(r'.+{', values[1]).group(0)[:-1]
                
                # extract if the state is 'initial' or 'accepting'
                try:
                    flag = re.search(r'{(\B|initial|accepting|initial,accepting)}', values[1]).group(0)[1:-1]
                except:
                    raise ValueError(f'invalid syntax {eachline}')
                
                states_list.append((state_name, 
                                    'initial' in flag, 
                                    'accepting' in flag))
            
            elif values[0] == 'transition': # for lines starting with 'transition'
                assert len(values[1:]) == 4 # there should be 4 attributes 
                
                src, tgt, sigma, guard = values[1:]
                sigma_event = event_list[sigma]
                guard_expression = expression.typecheck(guard)
                transitions_list.append((src, tgt, 
                                         sigma_event, 
                                         guard_expression))
            else:
                raise ValueError(f'syntax error in line: {eachline}')
    
    # now create an ERA object
    a = era.ERA(0) # create an empty ERA

    # add the events
    for s in event_list.values():
        a.events.append(s)
        a.transitions_on_event[s.name] = []
    
    # add the active clocks that will appear on guards
    for c in active_clocks:
        a.active_clocks.append(c)
    
    # create the states
    states_dict = dict() # store the link between the locations of the file
                         # and the indices of the states that will be added to a
    
    for q in states_list:
        q_state = a.add_state()
        states_dict[q[0]] = q_state
        
        if q[1] == True: # the state is initial
            a.make_initial(q_state.index())
        
        if q[2] == True: # the state is accepting
            a.make_final(q_state.index())

    # create the transitions
    for t in transitions_list:
        src = states_dict[t[0]]
        tgt = states_dict[t[1]]
        sigma = t[2]
        guard = t[3]
        a.add_transition(src, sigma, guard, tgt)

    return a
