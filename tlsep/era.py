from copy import deepcopy
import itertools

import event
import expression
from helper import is_contained, intersects
import symbolicword

class State:
    ''' 
    class for defining states of an automaton

    attributes --
    name : name of the state
    init : a boolean variable indicating whether the state is the initial state
    accepting : a boolean variable indicating whether the state is an accepting state

    init and accepting are optional attributes
    if not provided, they are set to False by default
    '''
    def __init__(self, 
                 statename: str, 
                 index: int,
                 init: bool = False, 
                 accepting: bool = False) -> None:
        self.name = statename
        self.__index = index
        self.init = init
        self.accepting = accepting
        self.dc = False # flag for don't care states
        self.status = True

    def __str__(self):
        return self.name
    
    def copy(self, index):
        return State(self.name, index, True if self.init else False, True if self.accepting else False)

    def get_name(self):
        return self.name
    
    def is_init(self):
        '''
        return True  if this state is the initial state,
        return False otherwise
        '''
        return self.init

    def is_accepting(self):
        '''
        return True  if this state is an accepting state,
        return False otherwise
        '''
        return self.accepting
    
    def index(self):
        return self.__index

class Transition:
    ''' class for describing transitions of an ERA

    attributes --
    src : a state
    '''
    def __init__(self, src: State, tgt: State,
                 event: event.Event, g: expression.Expression) -> None:
        self.src = src
        self.tgt = tgt
        self.guard = g
        self.event = event

    def __str__(self):
        return f'{self.src.name}:{self.tgt.name}:{self.event}:{self.guard}'

class ERA:
    '''
    an object of this class is an event recording automaton

    n : number of states
    m : number of events

    '''
    def __init__(self, n) -> None:
        self.nstates = n
        self.events = []
        self.active_clocks = []
        
        self.states = dict()
        self.transitions = [[] for i in range(self.nstates)]  # transitions[src][tgt] = [t1, t2]
        for i in range(n):
            self.states[i] = State('q' + str(i), i)
            self.transitions[i] = [[] for i in range(self.nstates)]
        self.curr_state = 0 # index of current state of the automaton
        self.transitions_on_event = dict()  # type = {e: [(src, tgt), (src, tgt)]}
        self.transitions_from_state_on_events = {}  # type = {src: {e: [g1, g2]}}
        self.transitions_on_letters_from_state = {}  #event_x_guard #type = {(e,g): {src: [tgt1, tgt2]}}
        
        self.is_deterministic = True    #currently not being updated when a transition is added or a product is constructed

    def __str__(self) -> str:
        output_str = f'number of states: {self.states_count()}'
        for e in self.events:
            output_str += f'\nevent:{e.name}{{'
            if e in self.active_clocks:
                output_str += 'active'
            output_str += '}'
        for q in self.states.values():
            if not q.status:
                continue
            output_str += f'\nlocation:{q}{{'
            if q.init:
                output_str += 'initial,'
            if q.accepting:
                output_str += 'accepting'
            if q.dc:
                output_str += "don't care"
            output_str += '}'
        for state_i in self.states.keys():
            if not self.states[state_i].status:
                continue
            for state_j in self.states.keys():
                if not self.states[state_j].status:
                    continue
                for each_transition in self.transitions[state_i][state_j]:
                    output_str += f'\ntransition:{each_transition}'
        output_str += '\n\ndeterministic? '
        if self.is_deterministic:
            output_str += 'Yes\n'
        else:
            output_str += 'No\n'
        return output_str

    def __mul__(self, a: object):
        assert self.events == a.events
        n_1 = self.nstates
        n_2 = a.nstates
        n = n_1 * n_2
        out_era = ERA(n)
        out_era.events = self.events[:]
        out_era.active_clocks = self.active_clocks[:]

        for i in range(n_1):
            for j in range(n_2):
                if self.states[i].init and a.states[j].init:
                    out_era.make_initial(i * n_2 + j)
                if self.states[i].accepting and a.states[j].accepting:
                    out_era.make_final(i * n_2 + j)
                if self.states[i].dc or a.states[j].dc:
                    out_era.states[i * n_2 + j].dc

                out_era.states[i * n_2 + j].status = self.states[i].status and a.states[j].status

        for i1, j1 in itertools.product(range(n_1), range(n_1)):
            for each_self_transition in self.transitions[i1][j1]:
                e = each_self_transition.event
                g = each_self_transition.guard
                for i2, j2 in itertools.product(range(n_2), range(n_2)):
                    for each_a_transition in a.transitions[i2][j2]:
                        src = out_era.states[i1 * n_2 + i2]
                        tgt = out_era.states[j1 * n_2 + j2]

                        if each_a_transition.event == e:
                            if each_a_transition.guard == g:
                                new_guard = g
                            else:
                                new_guard = expression.ConjExpression((g, each_a_transition.guard))

                            out_era.nd_add_transition(src, e, new_guard, tgt)
        
        if self.is_deterministic and a.is_deterministic:
            out_era.is_deterministic = True
        
        return out_era


    def states_count(self) -> int:
        ''' return the number of states present in an ERA

        NOTE: era.nstates does not represent this number
        '''
        return sum([1 for q in self.states.values() if q.status == True])
    
    def step(self, q: State, s: symbolicword.SymEvent) -> State:
        ''' given a guarded letter w:=(a,g), 
            this function executes one transition 
            of the ERA self and modifies the current state
            of self

            Arguments:
                q : a state in the ERA self
                w : a symbolic event

            returns:
                q_next : the state self reaches after reading w
                None   : if w cannot be read from q in self
        '''
        # q must be a valid state 
        if q is None: return None
        # assert q.status == True

        a = s.event
        g = s.guard
        for q1 in range(self.nstates):
            for t in self.transitions[q.index()][q1]:
                if t.event == a:
                    # intersection is sufficient since g is a region-word
                    if intersects(g, t.guard):
                        return t.tgt
                    
    def read_word(self, q_start, w: symbolicword.SymWord):
        '''input: start state, and a symbolic word

           output: q_tgt, the state self reaches after reading w from q_start
                   None, if w cannot be read from q in self
        '''
        if q_start is None: return None
        q = q_start

        for s in w.symbolic_word:
            q_next = self.step(q, s)
            if q_next is None:
                return None
            q = q_next
        return q
    
    def accepts(self, w: symbolicword.SymWord, q_src:State = None) -> bool:
        ''' check if a symbolic word is accepted by an ERA, from a state q_src

            q_src is optional; if undefined, by default, start from self.initstate

            (this is implemented ONLY for symbolic region-words)

            NOTE: for a region word w and an era A, 
                  one concretization of w is accepted by A iff
                  every concretization of w is accepted by A

            Arguments:
                w : a symbolic (region-)word and (optional) q_src: start state

            Returns:
                True : if every concretization of w is accepted by the ERA self
                False: otherwise
        '''
        q_src = q_src if q_src else self.initialstate
        q = self.read_word(q_src, w)

        if q is None:
            return False
        return q.accepting
    
    def complement(self):
        '''complement the automaton in-place (does not create a new automaton)
            this makes every accepting state non-accepting
            and every non-accepting state accepting
        '''
        if not self.is_deterministic:
            raise TypeError('era.py: the complement method currently supports only deterministic ERAs')

        for q in self.states.keys():
            self.states[q].accepting = not(self.states[q].accepting)

    def add_state(self) -> State:
        index_of_new_state = self.nstates
        old_nstates = self.nstates
        self.nstates += 1
        
        # add a new state and add it to the era
        assert index_of_new_state not in self.states.keys()
        new_state = State('q' + str(index_of_new_state), 
                                 index_of_new_state)
        self.states[index_of_new_state] = new_state
        
        # add transitions
        # step 1: no incoming transitions to the new state
        for each in range(old_nstates):
            self.transitions[each].append([])
        # step 2: no outgoing transitions from the new state
        self.transitions.append([[] for i in range(self.nstates)])
        
        return new_state

    def out_transitions(self, src: State):
        return self.transitions[src.index()]
    
    def has_transition(self, src: State, event: event.Event, guard: expression.Expression, tgt: State) -> bool:
        if guard.expr == 'True':
            for each_transition in self.transitions[src.index()][tgt.index()]:
                self.del_transition(each_transition)
            return False
        
        for each_transition in self.transitions[src.index()][tgt.index()]:
            if each_transition.event == event:
                if (each_transition.guard.expr == 'True' or 
                   each_transition.guard == guard):
                    return True
        return False

    def add_transition(self, src:State, event: event.Event, guard: expression.Expression, tgt: State) -> None:
        # if the guard is True, then we only keep this transition between
        # src and tgt on the letter event

        to_be_deleted = []
        for t in self.transitions[src.index()][tgt.index()]:
            if t.event == event:
                if (is_contained(guard, t.guard) or
                    t.guard.expr == 'True'):
                    return
                elif (is_contained(t.guard, guard) or
                    guard.expr == 'True'):
                    to_be_deleted.append(t)
        for each in to_be_deleted:
            self.del_transition(each)

        self.nd_add_transition(src, event, guard, tgt)
    
    def nd_add_transition(self, src: State, 
                          event: event.Event, 
                          guard: expression.Expression,
                          tgt: State) -> None:
        
        self.transitions[src.index()][tgt.index()].append(Transition(src, tgt, event, guard))
        self.transitions_on_event.setdefault(event.name, []).append((src.index(), tgt.index()))
        self.transitions_from_state_on_events.setdefault(src.index(), {}). setdefault(event.name, []).append(guard)
        self.transitions_on_letters_from_state.setdefault((event.name, guard.expr), {}). setdefault(src.index(), []).append(tgt.index())
       
    
    def del_state(self, state: State) -> None:
        state.status = False
        
        if state.accepting == True: 
            state.accepting = False

        # no outgoing transitions from state
        self.transitions[state.index()] = [[] for i in range(self.nstates)]

    def remove_sinks(self) -> None:
        ''' remove sink states from the automaton
            a sink state is a non-accepting state with only self-loops 
        '''
        sink_states = []
        for q in self.states.keys():
            for qp in self.states.keys():
                if ((q != qp) and 
                    (self.transitions[q][qp] != [])):
                    break
            else:
                sink_states.append(q)
        
        for q in sink_states:
            self.del_state(self.states[q])
    
    def make_initial(self, q_index: int) -> None:
        if q_index not in self.states.keys():
            raise ValueError('the state you are trying to make initial is not present in the automaton')
        self.states[q_index].init = True
        self.initialstate = self.states[q_index]

    def make_final(self, q_index: int) -> None:
        if q_index not in self.states.keys():
            raise ValueError('the state you are trying to make accepting is not present in the automaton')
        self.states[q_index].accepting = True

    def make_dc(self, q_index: int) -> None:
        if q_index not in self.states.keys():
            raise ValueError("the state you are trying to make don't care is not present in the automaton")
        self.states[q_index].dc = True

    def make_dc_states_accepting(self) -> None:
        for q_index in self.states.keys():
            if self.states[q_index].dc:
                self.states[q_index].dc = False
                self.states[q_index].accepting = True


    def find_incompatible_pairs(self) -> list:
        ''' returns a list of pairs (as a set) of indices that are incompatible'''

        def is_transition_to_incompatible(src1, src2, tgt: set):
            for transition_from_src1 in self.transitions[src1][list(tgt)[0]]:
                for transition_from_src2 in self.transitions[src2][list(tgt)[1]]:
                    if transition_from_src1.event == transition_from_src2.event and transition_from_src1.guard == transition_from_src2.guard:
                        return({src1,src2})
            for transition_from_src1 in self.transitions[src1][list(tgt)[1]]:
                for transition_from_src2 in self.transitions[src2][list(tgt)[0]]:
                    if transition_from_src1.event == transition_from_src2.event and transition_from_src1.guard == transition_from_src2.guard:
                        return({src1,src2})
                    
        incompatible_pairs = []
        
        n = len(self.states)

        # add every pair of {accepting, rejecting} in incompatible_pairs
        for i in range(n):
            for j in range(i+1, n):
                if ((not self.states[i].accepting and not self.states[i].dc) and (self.states[j].accepting)):
                    incompatible_pairs.append({i,j})
                elif ((not self.states[j].accepting and not self.states[j].dc) 
                       and (self.states[i].accepting)):
                    incompatible_pairs.append({i,j})

        # add pairs as long as you can
        while True:
            incompatible_pairs_c = incompatible_pairs[:]
            for i in range(n):
                for j in range(i+1,n):
                    if {i,j} in incompatible_pairs:
                        continue
                    for pair in incompatible_pairs:
                        # check for transition i -> pair[0] and j -> pair[1] or v.v.
                        new_pair = is_transition_to_incompatible(i, j, pair)
                        if new_pair is not None:
                            incompatible_pairs_c.append(new_pair)
                        
            # condition to stop the while loop : if no new pair is added
            if len(incompatible_pairs) == len(incompatible_pairs_c):
                break
            incompatible_pairs = incompatible_pairs_c[:]
        return incompatible_pairs

    def find_maximal_compatible_sets(self) -> list:
        ''' returns a list of sets of indices
        for which the corresponding states are maximal and pairwise compatible'''
         
        n = len(self.states)
        incompatible_pairs = self.find_incompatible_pairs()

        maximal_sets = [{index for index in range(n)}]    #keys to the states
        
        change = True
        while change:
            change = False
            maximal_sets_c = maximal_sets[:]   
            for element in maximal_sets:
                for x,y in incompatible_pairs:
                    if ((x in element) and (y in element)):
                        change = True
                        maximal_sets_c.remove(element)
                        if all(not (element-{x}).issubset(t) for t in maximal_sets_c):
                            maximal_sets_c.append(element-{x}) 
                        if all(not (element-{y}).issubset(t) for t in maximal_sets_c):
                            maximal_sets_c.append(element-{y})
                        if change:
                            break
            maximal_sets = maximal_sets_c
        
        return maximal_sets

    def description_for_tchecker(self, P: str):
        description = ''
        
        # define the process
        description += f'process:{P}' + '{}\n'
        
        # define locations
        for j in self.states.keys():   # keys are indices
            description += f'location:{P}:l{j}{{'
            attributes = []
            if self.states[j].init:
                attributes.append('initial:')
            # no attribute for accepting states
            if self.states[j].accepting:
                attributes.append(f'labels:{P}accepting')
            description += ':'.join(attributes)
            description += '} \n'
        
        description += '\n'
        
        # define edges
        for src_index in range(self.nstates):
            for tgt_index in range(self.nstates):
                for each_transition in self.transitions[src_index][tgt_index]:
                    e = each_transition.event
                    g = each_transition.guard.expr
                    if e in self.active_clocks:
                        # print(f'found {e} to be active')
                        if g == 'True':
                            description += f'edge:{P}:l{src_index}:l{tgt_index}:{e.name}{{do:{e.name}=0}}\n'
                        else:
                            description += f'edge:{P}:l{src_index}:l{tgt_index}:{e.name}{{provided:{g} : do:{e.name}=0}}\n'
                    else:
                        # print(f'found {e} to be not active')
                        if g == 'True':
                            description += f'edge:{P}:l{src_index}:l{tgt_index}:{e.name}{{}}\n'
                        else:
                            description += f'edge:{P}:l{src_index}:l{tgt_index}:{e.name}{{provided:{g}}}\n'

        return description

    def write_era_to_file(self, outfile: str, sysname: str = 'my_sys', nb_processes: int = 1) -> None:
        ''' write an (D)ERA to a file in TChecker syntax
            arguments:
                a       : a (D)ERA that is to be written
                outfile : file where the automaton is to be written
            
            returns:
                None (the automaton gets written on the file 'outfile')
        '''
        with open(f'{outfile}', 'w') as outfile:

            # system declaration - whatever that is
            outfile.write(f'system:{sysname}\n\n')

            # event declaration
            for e in self.events:
                outfile.write(f'event:{e.name}\n')
            
            outfile.write('\n')
            
            #clock declaration -- same as event names
            for e in self.active_clocks:
                outfile.write(f'clock:1:{e.name}\n')

            outfile.write('\n')
            
            # iterate over each process
            for i in range(nb_processes):
                # process declaration
                outfile.write(f'process:P{i}\n')

                # locations -- in our class each state is a tuple (statename, index)
                for j in self.states.keys():   # keys are indices
                    outfile.write(f'location:P{i}:l{j}{{')
                    attributes = []
                    if self.states[j].init:
                        attributes.append('initial:')
                    # no attribute for accepting states
                    if self.states[j].accepting:
                        attributes.append('labels: accepting')
                    outfile.write(':'.join(attributes))
                    outfile.write('} \n')

                outfile.write('\n')

                for src_index in range(self.nstates):
                    for tgt_index in range(self.nstates):
                        for each_transition in self.transitions[src_index][tgt_index]:
                            e = each_transition.event
                            g = each_transition.guard.expr
                            if e in self.active_clocks:
                                # print(f'found {e} to be active')
                                outfile.write(f'edge:P{i}:l{src_index}:l{tgt_index}:{e.name}{{provided:{g} : do:{e.name}=0}}\n')
                            else:
                                # print(f'found {e} to be not active')
                                outfile.write(f'edge:P{i}:l{src_index}:l{tgt_index}:{e.name}{{provided:{g}}}\n')

