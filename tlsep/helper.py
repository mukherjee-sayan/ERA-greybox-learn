from z3 import *

import expression

def encode_constraint(g: expression.SimpleExpression,
                      clock_list: dict):
    ''' given a constraint g, 
        encode g into a constraint to be used in z3
    '''
    clk = g.event.get_event()
    
    if (g.cmp == 'lt'):
        encoded_constraint = clock_list[clk] < g.bound()
    elif (g.cmp == 'le'):
        encoded_constraint = clock_list[clk] <= g.bound()
    elif (g.cmp == 'eq'):
        encoded_constraint = clock_list[clk] == g.bound()
    elif (g.cmp == 'ge'):
        encoded_constraint = clock_list[clk] >= g.bound()
    elif (g.cmp == 'gt'):
        encoded_constraint = clock_list[clk] > g.bound()
    else:
        raise ValueError
    return encoded_constraint

def create_vars_for_clks(g: expression.ConjExpression,
                         list_of_clocks: dict) -> None:
    '''given a constraint g,
        add a Real variable to list_of_clocks
        corresponding to every clock present in g
    '''
    atoms_of_g = g.conjuncts() # all the atomic constraints present in g

    for each in atoms_of_g:
        nameofevent = each.event.get_event()
        if nameofevent not in list_of_clocks.keys():
            list_of_clocks[nameofevent] = Real(nameofevent)


def constraint_to_clause(g: expression.ConjExpression,
                         list_of_clocks: dict):
    ''' given a (conjunctive) expression g and the dict containing 
                                    a real variable per clock present in g
        return a clause that encodes the constraint g
    '''
    atoms_of_g = g.conjuncts()
    phi = True

    for each in atoms_of_g:
        phi = And(phi, encode_constraint(each, list_of_clocks))
    
    return phi

def is_contained(g1: expression.ConjExpression, g2: expression.ConjExpression) -> bool:
    '''return TRUE  if g1 is contained in g2
              FALSE otherwise
    '''
    list_of_clocks = {}
    create_vars_for_clks(g1, list_of_clocks)
    create_vars_for_clks(g2, list_of_clocks)

    g1_c = constraint_to_clause(g1, list_of_clocks)
    g2_c = constraint_to_clause(g2, list_of_clocks)

    s = Solver()
    for x in list_of_clocks.keys():
        s.add(list_of_clocks[x] >= 0)
    s.add(Not(Implies(g1_c, g2_c)))
    return (str(s.check()) == 'unsat')


def intersects(g1: expression.ConjExpression, g2: expression.ConjExpression) -> bool:
    '''returns TRUE  if g1 intersects g2, 
               FALSE otherwise
    '''
    list_of_clocks = {}
    create_vars_for_clks(g1, list_of_clocks)
    create_vars_for_clks(g2, list_of_clocks)

    g1_c = constraint_to_clause(g1, list_of_clocks)
    g2_c = constraint_to_clause(g2, list_of_clocks)

    s = Solver()
    for x in list_of_clocks.keys():
        s.add(list_of_clocks[x] >= 0)
    s.add(And(g1_c, g2_c))

    return (str(s.check()) == 'sat')
    