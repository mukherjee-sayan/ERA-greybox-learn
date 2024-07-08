import event
import itertools

class Expression:
    def __init__(self, untyped_expr: str) -> None:
        self.expr = untyped_expr.replace(" ", "")
        self.type = None

    def __str__(self) -> str:
        return self.expr

    def __eq__(self, __o: object) -> bool:
        pass

    def type(self) -> str:
        return self.type

    def conjuncts(self):
        pass

    def var(self):
        pass
    
    def get_event(self):
        pass

    def bound(self):
        pass

    def op_str(self):
        pass

class TrueExpression(Expression):
    def __init__(self, expr: str) -> None:
        super().__init__(expr)
        assert self.expr == 'True'
        self.type = 'True'

    def __eq__(self, __o: object) -> bool:
        if type(__o) == TrueExpression:
            return self.expr == __o.expr 
        else:
            return False
   
    def conjuncts(self):
        return []

    def var(self):
        return None
    
    def get_event(self):
        raise TypeError('expression.py: event not defined for TrueExpression')

    def bound(self):
        return self.value

    def op_str(self):
        raise TypeError('expression.py: op_str not defined for TrueExpression')

class IntExpression(Expression):
    def __init__(self, v: int) -> None:
        super().__init__(str(v))
        if type(v) != int:
            raise TypeError("expected integer as an input")
        self.value = v
        self.type = 'int'

    def __eq__(self, __o: object) -> bool:
        if type(__o) == IntExpression:
            return self.value == __o.value
        else:
            return False

    def conjuncts(self):
        raise TypeError('expression.py: conjuncts not defined for IntExpression')
    
    def var(self):
        return None
    
    def get_event(self):
        raise TypeError('expression.py: event not defined for IntExpression')

    def bound(self):
        return self.value

    def op_str(self):
        raise TypeError('expression.py: op_str not defined for IntExpression')

class VarExpression(Expression):
    def __init__(self, v: str) -> None:
        super().__init__(v)
        if type(v) != str:
            raise TypeError("expected string as an input")
        self.type = 'str'
    
    def __eq__(self, __o: object) -> bool:
        if type(__o) == VarExpression:
            return self.expr == __o.expr
        else:
            return False

    def conjuncts(self):
        raise TypeError('expression.py: conjuncts not defined for VarExpression')

    def var(self):
        return event.Event(self.expr)
    
    def get_event(self):
        pass

    def bound(self):
        raise TypeError('expression.py: bound not defined for VarExpression')

    def op_str(self):
        raise TypeError('expression.py: op_str not defined for VarExpression')
    
def reverse(cmp: str) -> str:
    ''' this function reverses the operator

        Arguments:
            cmp  - a comparator operator, e.g. <=, >= etc

        Returns:
            <= if cmp is >=    
            <  if cmp is >    
            >= if cmp is <=
            >  if cmp is <
            =  if cmp is =
    '''
    if cmp == 'ge':
        return 'le'
    elif cmp == 'gt':
        return 'lt'
    elif cmp == 'le':
        return 'ge'
    elif cmp == 'lt':
        return 'gt'
    elif cmp == 'eq':
        return 'eq'
    else:
        raise ValueError('unexpected operator found while reversing')

class SimpleExpression(Expression):
    def __init__(self, v: str) -> None:
        super().__init__(v)
        if '&&' in v:
            raise ValueError('expression.py: unexpected conjunction found in SimpleExpression, use ConjExpression instead')
        if '<=' in v:
            self.cmp = 'le'
            v_str = v.split('<=')
        elif '<' in v:
            self.cmp = 'lt'
            v_str = v.split('<')
        elif '>=' in v:
            self.cmp = 'ge'
            v_str = v.split('>=')
        elif '>' in v:
            self.cmp = 'gt'
            v_str = v.split('>')
        elif '==' in v:
            self.cmp = 'eq'
            v_str = v.split('==')
        else:
            raise ValueError('expression.py: no eligible operator found')

        try:
            self.event, self.value = event.Event(v_str[0]), IntExpression(int(v_str[1]))
        except:
            self.event, self.value = event.Event(v_str[1]), IntExpression(int(v_str[0]))
            self.cmp = reverse(self.cmp)
                
        self.type = 'simple'

    def __eq__(self, __o: object) -> bool:
        if type(__o) == SimpleExpression:
            return self.get_event() == __o.get_event() and self.op_str() == __o.op_str() and self.bound() == __o.bound()
        elif type(__o) == ConjExpression:
            return (__o.nconjuncts == 1 and __o.list_of_constraints[0] == self)

    def extract_bounds(self) -> int:
        ''' this returns the lower and upper bounds 
            of the event present in the expression

            Arguments:
                self - a simple expression x ~ c

            Returns:
                (lower, upper) - lower = c, if ~ is = or >=
                                       = None, otherwise
                                 upper = c, if ~ is = or <=
                                       = None, otherwise
        '''
        lower, upper = None, None
        if self.cmp == 'eq':
            lower = self.value.value
            upper = self.value.value
        elif self.cmp in ['le', 'lt']:
            upper = self.value.value
        elif self.cmp in ['ge', 'gt']:
            lower = self.value.value
        else:
            raise ValueError('unexpected type of SimpleExpression')
        return (lower, upper)


    def conjuncts(self):
        return [self]

    def var(self):
        return self.event

    def get_event(self):
        return self.event

    def bound(self):
        return self.value.value #returns an integer

    def op_str(self):
        return self.cmp

class ConjExpression(Expression):
    def __init__(self, l_constraints) -> None:
        list_of_simple_constraints = []
        if (type(l_constraints) != tuple):
            assert type(l_constraints) == str
            v = l_constraints
            super().__init__(v)
            v_str = v.split('&&')
            list_of_simple_constraints = []
            for each in v_str:
                list_of_simple_constraints.append(SimpleExpression(each))
            self.list_of_constraints = optimize_constraints(list_of_simple_constraints)

            self.type = 'conjunctive'
            self.nconjuncts = len(self.list_of_constraints)
        else:
            assert type(l_constraints) == tuple
            for constraint in list(l_constraints):
                if constraint.type == "conjunctive":
                    list_of_simple_constraints += constraint.list_of_constraints
                elif constraint.type == "simple":
                    list_of_simple_constraints.append(constraint)
                elif constraint.type == "True":
                    pass
                else:
                    raise TypeError("unexpected type of constraint")
            if len(list_of_simple_constraints) == 0:
                self.list_of_constraints = [typecheck('True')]
            else:
                self.list_of_constraints = optimize_constraints(list_of_simple_constraints)
            self.type =  "conjunctive"
            self.nconjuncts = len(self.list_of_constraints)
        self.expr = self.list_of_constraints[0].expr
        for each in range(1, len(self.list_of_constraints)):
            self.expr += '&&' + self.list_of_constraints[each].expr
    
    
    def __iter__(self):
        return SimpleExpressionIter(self)    

                
    def __eq__(self, __o: object) -> bool:
        if type(__o) == ConjExpression:
            for i in range(self.nconjuncts):
                for j in range(__o.nconjuncts):
                    if self.list_of_constraints[i] == __o.list_of_constraints[j]:
                        break
                else:
                    return False
            for j in range(__o.nconjuncts):
                for i in range(self.nconjuncts):
                    if self.list_of_constraints[i] == __o.list_of_constraints[j]:
                        break
                else:
                    return False
            return True
        elif type(__o) == SimpleExpression:
            return (self.nconjuncts == 1 and self.list_of_constraints[0] == __o)

    def conjuncts(self):
        return self.list_of_constraints

    def var(self):
        raise TypeError('expression.py: var not defined for ConjExpression')
    
    def get_event(self):
        raise TypeError("expression.py: get_event not defined for ConjExpression")


    def bound(self):
        raise TypeError("expression.py: bound not defined for ConjExpression")

    def op_str(self):
        raise TypeError("expression.py: op_str not defined for ConjExpression")

def replace_by_eq(list_of_simple_constraints: list[SimpleExpression]):
    if len(list_of_simple_constraints)<=1:    # no constraint on event e
        return list_of_simple_constraints
    while True:
        new_list = list_of_simple_constraints[:]
        n = len(list_of_simple_constraints)
        for i,j in itertools.product(range(n), range(n)):
            if i < j:
                if ((list_of_simple_constraints[i].event.name == list_of_simple_constraints[j].event.name)
                    and (list_of_simple_constraints[i].bound() == list_of_simple_constraints[j].bound())):
                    if ((list_of_simple_constraints[i].cmp == 'ge' and list_of_simple_constraints[j].cmp == 'le')
                        or (list_of_simple_constraints[i].cmp == 'le' and list_of_simple_constraints[j].cmp == 'ge')):
                        new_constraint = SimpleExpression(list_of_simple_constraints[i].event.name + '==' + str(list_of_simple_constraints[i].bound()))
                        list_of_simple_constraints[i] = new_constraint
                        list_of_simple_constraints.pop(j)
                        break
        if len(new_list) == len(list_of_simple_constraints):
            return list_of_simple_constraints
        
def remove_dups(list_of_simple_constraints: list[SimpleExpression]):
    if len(list_of_simple_constraints)<=1:    # no constraint on event e
        return list_of_simple_constraints
    while True:
        new_list = list_of_simple_constraints[:]
        n = len(list_of_simple_constraints)
        for i,j in itertools.product(range(n), range(n)):
            if (i != j and list_of_simple_constraints[i] == list_of_simple_constraints[j]):
                list_of_simple_constraints.pop(j)
                break
        if len(new_list) == len(list_of_simple_constraints):
            return list_of_simple_constraints

def optimize_constraints(list_of_simple_constraints: list):    
    list_of_optimized_constraints = remove_dups(list_of_simple_constraints)
    list_of_optimized_constraints = replace_by_eq(list_of_simple_constraints)
    return list_of_optimized_constraints




class SimpleExpressionIter:
    def __init__(self, conj: ConjExpression) -> None:
        self._list_of_conjuncts = conj.list_of_constraints
        self.len = conj.nconjuncts
        self._current_index = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self._current_index < self.len:
            member = self._list_of_conjuncts[self._current_index]
            self._current_index += 1
            return member

        raise StopIteration


def typecheck(g: str) -> Expression:
    if g == 'True':
        return TrueExpression(g)
    elif '&&' in g:
        return ConjExpression(g)
    elif '<' in g or '>' in g or '==' in g:
        return SimpleExpression(g)
    else:
        try:
            return IntExpression(int(g))
        except:
            return VarExpression(g)

