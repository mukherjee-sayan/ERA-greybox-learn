from collections import defaultdict

import event
import expression

class SymEvent:
    def __init__(self, inp_event: str) -> None:
        if inp_event[0] + inp_event[-1] != '()':
            if inp_event == 'EPSILON':
                event_str = 'EPSILON'
                guard = 'True'
            else:
                raise TypeError('SymEvent: invalid symbolic event')
        else:    
            event_str, guard = inp_event[1:-1].split(',')
        self.event = event.Event(event_str)
        self.guard = expression.typecheck(guard)

    @classmethod
    def constructUsingEventGuard(cls, a: event.Event, 
                                      g: expression.ConjExpression):
        a_str = a.name
        g_str = g.expr
        return cls(f'({a_str},{g_str})')

    def __str__(self) -> str:
        return f'({self.event}, {self.guard})'
    
    def get_event(self):
        return self.event
    
    def get_guard(self):
        return self.guard
    
    def __eq__(self, __o: object) -> bool:
        return (self.event == __o.event and self.guard == __o.guard)


class SymWord:
    def __init__(self, list_of_symbolic_events: list[SymEvent]) -> None:
        self.symbolic_word = []
        self.is_epsilon = False
        for symbolic_event in list_of_symbolic_events:
            if symbolic_event.event.get_event() == 'EPSILON':
                if len(list_of_symbolic_events) != 1:
                    raise TypeError('symbolicword.py: unexpected argument to SymWord, a symbolic word of length >1 is not expected to have epsilon in it')
                self.is_epsilon = True
            self.symbolic_word.append(symbolic_event)
        self.len = len(self.symbolic_word)

    def __str__(self) -> str:
        return_str = ', '.join([str(symbolic_event) for symbolic_event in self.symbolic_word])
        return return_str
    
    def __eq__(self, __o: object) -> bool:
        len_of_o = len(__o.symbolic_word)
        if len_of_o != len(self.symbolic_word):
            return False
        for index, symbolic_event in enumerate(self.symbolic_word):
            if symbolic_event != __o.symbolic_word[index]:
                return False
        return True
    
    def __add__(self, __o: object):
        w = SymWord([])
        if not self.is_epsilon:
            w.symbolic_word += self.symbolic_word
        if not __o.is_epsilon:
            w.symbolic_word += __o.symbolic_word
        if self.is_epsilon and __o.is_epsilon:
            w = SymWord([SymEvent('EPSILON')])
        w.len = len(w.symbolic_word)
        return w

    def __iter__(self):
        return SymEventIter(self)

    def __getitem__(self, id) -> SymEvent:
        return self.symbolic_word[id]
    
class SymEventIter:
    def __init__(self, symword: SymWord) -> None:
        self._symbolic_word = symword.symbolic_word
        self.len = symword.len
        self._current_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._current_index < self.len:
            member = self._symbolic_word[self._current_index]
            self._current_index += 1
            return member

        raise StopIteration
    
def sort_symword_list(list_of_symwords: list[SymWord]) -> list[SymWord]:
    symword_dict = defaultdict(list)
    for word in list_of_symwords:
        symword_dict[word.len].append(word)
    sorted_symword_dict = sorted(symword_dict.items())

    sorted_list = []
    for i in range(len(sorted_symword_dict)):
        sorted_list += sorted_symword_dict[i][1]
    return sorted_list 
