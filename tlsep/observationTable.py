import itertools
import copy
from collections import defaultdict
from prettytable import PrettyTable

import expression
import symbolicword
import era
import acceptance
import stats

def create_list_of_regions(m: int, events_list: list):
    ''' create a list of all the regions 
        
        arguments:

        m        = max constant
        n_clocks = number of clocks
    '''
    regions = []
    regions_per_clock = [[] for x in range(len(events_list))] 
    for j in range(len(events_list)): # for every clock
        x = str(events_list[j])
        for i in range(m):
            regions_per_clock[j].append(expression.SimpleExpression(f'{x}=={i}'))
            regions_per_clock[j].append(expression.ConjExpression(f'{x}>{i}&&{x}<{i+1}'))
        regions_per_clock[j].append(expression.SimpleExpression(f'{x}=={m}'))
        regions_per_clock[j].append(expression.SimpleExpression(f'{x}>{m}'))
    for region in itertools.product(*regions_per_clock):
        regions.append(expression.ConjExpression(region))
    return regions

class ObservationTable:
    def __init__(self, sul: era.ERA, m: int):
        self.L = sul.events[:] # events
        active_clocks = sul.active_clocks[:]
        R = create_list_of_regions(m, active_clocks) # set of all regions

        self.A = [symbolicword.SymEvent.constructUsingEventGuard(a, g) 
                                    for a, g in itertools.product(self.L, R)]
        
        self.S = [] # rows
        self.E = [] # columns
        self.T = defaultdict(tuple)

        self.T_symbolic = {}    # keep track which string to which symbolic word
        
        self.sul = sul
        # compute and store the complement of sul (for membership queries)
        sul_copy = copy.deepcopy(sul)

        sul_copy.complement()
        self.sul_c = sul_copy

        # add the empty word
        empty_word = symbolicword.SymWord([symbolicword.SymEvent('EPSILON')])
        self.S.append(empty_word)
        self.E.append(empty_word)

        self.inconsistent_words = {}
        self.read_word_in_sul = {}

        # check membership of epsilon
        ans = acceptance.check(self.sul, empty_word)
        stats.MQ += 1
        stats.MQc += 1
        if ans == True:
            self.T[str(empty_word)] += (1, )
        else:
            self.T[str(empty_word)] += (0, )
        
        self.T_symbolic[str(empty_word)] = empty_word
        self.read_word_in_sul[str(empty_word)] = self.sul.initialstate


    def __str__(self, print_whole_table = False):
        table = PrettyTable()
        table.field_names = ['None'] + [str(w) for w in self.E]
        
        # print only the S part
        if not print_whole_table:
            for i in range(len(self.S)):
                table.add_row([str(self.S[i])] + [self.T[str(self.S[i])][j]for j in range(len(self.E))], divider=True)
        
        # print the whole table
        elif print_whole_table:
            for i in self.T.keys():
                if self.T[i] != ():
                    table.add_row([i] + [self.T[i][j] for j in range(len(self.E))], divider=True)
                else:
                    # uncomment the following line to print the 'empty' rows
                    # table.add_row([i] + ['?' for j in range(len(self.E))], divider=True)
                    continue
            
        table.align = 'l'
        table.align['None'] = 'c'
        return str(table)

    def evaluate_and_add(self, p: symbolicword.SymWord, 
                               s: symbolicword.SymWord = None) -> tuple:
        '''given a guarded word, 
            query the sul and update the entry in the table
        '''

        if s is None:
            s = symbolicword.SymWord([symbolicword.SymEvent('EPSILON')])
        
        w = p + s
        if str(p) in self.inconsistent_words:
            self.inconsistent_words[str(w)] = 1
            return ('?', )
        # check if w is empty
        if acceptance.is_empty(w):
            self.inconsistent_words[str(w)] = 1
            return ('?', )
        
        # Membership query (check if w intersects sul)

        stats.MQ += 1
        if str(w) in self.read_word_in_sul:
            q = self.read_word_in_sul[str(w)]
            return (1, ) if (q is not None and q.accepting) else (0, )
        
        stats.MQc += 1 
        if len(w.symbolic_word) == 1:
            w1 = symbolicword.SymWord([symbolicword.SymEvent('EPSILON')])
        else:
            w1 = symbolicword.SymWord(w.symbolic_word[:-1])

        if str(w1) in self.read_word_in_sul:
            q1 = self.read_word_in_sul[str(w1)]
            if q1 is None: 
                self.read_word_in_sul[str(w)] = None
                return (0, )
            
            a = w.symbolic_word[-1]
            q_f = self.sul.step(q1, a)
            self.read_word_in_sul[str(w)] = q_f

            if q_f is None:
                self.read_word_in_sul[str(w)] = None
                return (0, )
            
        else:
            q_f = self.sul.read_word(self.sul.initialstate, w)
            self.read_word_in_sul[str(w)] = q_f

            if q_f is None:
                self.read_word_in_sul[str(w)] = None
                return (0, )
            
        ans = q_f.accepting
        
        # intersection is empty iff w is not in L
        if ans == True:
            return (1, )
        elif ans == False:
            return (0, )


    def check_and_update_row(self, prefix: symbolicword.SymWord) -> bool:
        ''' input : a symbolic word
                    likely a new/old element in self.S or in S.A

            output: True if s is a new entry to the table, else False

            additionally, if True, update the entries of the new row
        '''
        
        if str(prefix) not in self.T.keys():
            # first, check if prefix is already empty
            ans = self.evaluate_and_add(prefix)
            if ans == ('?', ):
                self.T[str(prefix)] = tuple(['?' for i in range(len(self.E))])
                self.T_symbolic[str(prefix)] = prefix
                return 
            # if not, add entry corr. to first column, aka EPSILON
            self.T_symbolic[str(prefix)] = prefix
            self.T[str(prefix)] += ans
            
            # now check membership for every column other than (EPSILON, True)
            for s in range(1, len(self.E)):
                suffix = self.E[s]
                ans = self.evaluate_and_add(prefix, suffix)
                self.T[str(prefix)] += ans
            return True
        return False
    
    def add_S_dot_sigma(self, s_list: list = None) -> None:
        s_to_be_added = s_list if s_list is not None else self.S
        for prefix in s_to_be_added:
            for a in self.A:
                s_dot_a = prefix + symbolicword.SymWord([a])
                self.check_and_update_row(s_dot_a)

    def update_new_column(self, e: symbolicword.SymWord):
        for row in self.T:
            p = self.T_symbolic[row]
            ans = self.evaluate_and_add(p, e)
            self.T[str(p)] += ans
    
    def close_table(self) -> bool:
        ''' if there exists a row in S.Sigma that is 
            not present in S, then add this row to S

            returns:
                True  - if new row got added to S
                False - otherwise
        '''
        new_additions = False
        values_of_S = [self.T[str(p)] for p in self.S]
        temp_S = [] # temporarily store the prefixes to be added to S
        temp_S_values = set() # store the values of T of prefixes in temp_S
        for s in self.S:
            for a in self.A:
                p = s + symbolicword.SymWord([a])
                if self.T[str(p)] == ():
                    raise NotImplementedError
                    continue
                if (self.T[str(p)] not in values_of_S and 
                    self.T[str(p)] not in temp_S_values):
                    temp_S.append(p)
                    temp_S_values.add(self.T[str(p)])
        if len(temp_S) != 0:
            self.S += temp_S
            self.add_S_dot_sigma(temp_S)
            new_additions = True
        return new_additions

    def make_close_and_consistent(self) -> None:
        ''' this method makes an observation table closed and consistent
        '''
        closed = False
        consistent = True
        while (not closed or not consistent):
            while not closed:
                something_new_got_added_making_close = self.close_table()
                closed = False if something_new_got_added_making_close else True

            
            something_new_got_added_making_consistent = self.consistent_table()
            consistent = True
            closed = False if something_new_got_added_making_consistent else True

    
    def consistent_table(self) -> bool:
        ''' if there exist two rows s1, s2 in S such that 
        T[s1] = T[s2], but for some a in S.Sigma, 
        T[s1.a] != T[s2.a], then find the suffix w in E such that
        T[s1.a][w.index()] != T[s2.a][w.index()], and add a.w in E.

            returns:
                True  - if new column got added to E
                False - otherwise
        '''
        def find_problematic_suffix(p1: symbolicword.SymWord, p2: symbolicword.SymWord):
            for index, e in enumerate(self.E):
                if self.T[str(p1)][index] != self.T[str(p2)][index]:
                    return e
            
        new_additions = False
        for i in range(len(self.S)):
            for j in range(i+1,len(self.S)):
                s1 = self.S[i]
                s2 = self.S[j]
                if self.T[str(s1)] == self.T[str(s2)]:
                    for a in self.A:
                        p1 = s1 + symbolicword.SymWord([a])
                        p2 = s2 + symbolicword.SymWord([a])
                        assert ((str(p1) in self.T.keys()) and (str(p1) in self.T.keys()))
                        if self.T[str(p1)] != self.T[str(p2)]:                            
                            # we consider the case when the inequality is due
                            # to one of the prefixes (p1 or p2) becoming empty

                            problematic_suffix = None
                            if self.T[str(p1)] == () or self.T[str(p2)] == ():
                                problematic_suffix = symbolicword.SymWord([symbolicword.SymEvent('EPSILON')])
                            # now the case when the distinction 
                            # is not due to emptiness

                            if problematic_suffix is None:
                                problematic_suffix = find_problematic_suffix(p1, p2)
                            suffix = symbolicword.SymWord([a]) + problematic_suffix

                            self.E.append(suffix)
                            self.update_new_column(suffix)
                            new_additions = True
                            return new_additions
        return new_additions
    
    def add_all_prefixes_to_S(self, w: symbolicword.SymWord) -> None:
        for i in range(len(w.symbolic_word)):
            prefix = symbolicword.SymWord(w.symbolic_word[:i+1])
            for s in self.S:
                if (prefix == s):
                    break
            else:   # if prefix not in self.S:
                self.S.append(prefix)
                self.check_and_update_row(prefix)
                self.add_S_dot_sigma([prefix])
    
    def add_ws_to_E(self, w: symbolicword.SymWord, hypothesis: era.ERA,
                    states_dict: dict, sul_accepts_w: bool) -> None:
        ''' perform a binary search on the length of w
            to find the shortest suffix of w that causes the inconsistency,
            that is, find the last position i such that w = u_i . v_i
            and (i) self.T[s] = self.T[u_i] (where, s \in S is such that
                                             self.T[s] = self.T[u_i])
                (ii) self.T[s.v_i] =/= self.T[w]
            then add v_i to self.E and update the column
        '''
        ws = None

        left = 0
        right = len(w.symbolic_word) - 1
        
        while True:
            pos = (right + left) // 2

            # construct the prefix u
            u = symbolicword.SymWord(w.symbolic_word[:pos])
            v = symbolicword.SymWord(w.symbolic_word[pos:])
            
            q = hypothesis.states[0]
            assert q.init
            for s in u.symbolic_word:
                q_new = hypothesis.step(q, s)
                q = q_new

            for row in states_dict.keys():
                if states_dict[row] == q.index():
                    row_for_u = row
            assert row_for_u is not None
            
            # search for the row in S that matches row_for_u
            s = None
            for prefix in self.S:
                if self.T[str(prefix)] == row_for_u:
                    s = prefix 
                    break
            else:
                raise NotImplementedError('no row in S matched with u!')
            
            new_word = s + v

            stats.MQ += 1
            if (not (acceptance.is_empty(new_word)) and self.sul.accepts(new_word) == sul_accepts_w):
                left = pos + 1
                if right < left:
                    ws = symbolicword.SymWord(v.symbolic_word[1:])
                    break
            else:
                right = pos - 1
                if right < left:
                    ws = v
                    break

        if len(ws.symbolic_word) == 0:
            ws = symbolicword.SymWord([symbolicword.SymEvent('EPSILON')])

        if ws not in self.E:
            self.E.append(ws)
            self.update_new_column(ws)

    def add_cex(self, w:symbolicword.SymWord, hypothesis: era.ERA, 
                accepted_by_sul: bool, states_dict: dict, add_all_prefixes: bool = False) -> None:
        # we implement two strategies for processing counterexamples
        
        # option 1: add all prefixes of counterexample to S
        if add_all_prefixes == True:
            stats.all_prefixes += 1
            self.add_all_prefixes_to_S(w)
        
        # option 2: compute the witness suffix (ws) and add it to E
        elif not add_all_prefixes:
            stats.rs_calls += 1
            self.add_ws_to_E(w, hypothesis, states_dict, accepted_by_sul)
        
        else:
            raise ValueError('unsupported strategy for handling counterexamples')

    def add_columns(self, w: symbolicword.SymWord) -> None:
        for i in range(len(w.symbolic_word)-1, -1, -1):
            suffix = symbolicword.SymWord(w.symbolic_word[i:])
            # check if suffix is already in E
            for e in self.E:
                if e == suffix:
                    break
            else:   # suffix is new; add it to E
                self.E.append(suffix)
                self.update_new_column(suffix)

    def get_distinct_rows(self):
        distinct_rows = defaultdict(list)
        sorted_symword_list = symbolicword.sort_symword_list(self.S)
        assert (len(self.S) == len(sorted_symword_list))
        for s in sorted_symword_list:
            distinct_rows[self.T[str(s)]].append(s)

        return [r[0] for r in distinct_rows.values()]

    def generate_3era(self, use_distinct_rows: bool = True) -> era.ERA:
        # if want to generate 3ERA using whole Self.S, set the flag 'use_distinct_rows' to False

        ''' generate a candidate 3ERA compatible with the observation table

        Returns:
            a : a 3ERA 
        '''
        distinct_rows = self.get_distinct_rows() if use_distinct_rows else self.S

        a = era.ERA(len(distinct_rows)) # no. of states = no. of distinct rows in S
        q_dc = None
        
        a.events = self.L[:]
        a.active_clocks = self.sul.active_clocks[:]
        states_dict = dict() # store which rows the states of a correspond to
        for q_index in range(len(distinct_rows)):
            states_dict[self.T[str(distinct_rows[q_index])]] = q_index

        a.make_initial(0)   # make the first row initial
        for i in range(len(distinct_rows)):
            if self.T[str(distinct_rows[i])][0] == 1:
                a.make_final(i)
            elif self.T[str(distinct_rows[i])][0] == '?':
                a.make_dc(i)
                q_dc = a.states[i]

        # add transitions based on S.Sigma
        for i in range(len(distinct_rows)):
            for sigma in self.A:
                prefix = distinct_rows[i] + symbolicword.SymWord([sigma])
                val = self.T[str(prefix)]
                if val == ():
                    a.nd_add_transition(a.states[i], sigma.event, 
                                        sigma.guard, q_dc)
                else:
                    a.nd_add_transition(a.states[i], sigma.event, 
                                        sigma.guard, a.states[states_dict[val]])
        
        # complete the 3ERA: if dc state is not None, add self loops
        if q_dc is not None:
            for sigma in self.A:
                a.nd_add_transition(q_dc, sigma.event, sigma.guard, q_dc)

        return a, states_dict