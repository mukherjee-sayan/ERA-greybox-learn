class Event:
    '''when initializing a Event,
        all whitespaces are removed from the name 
    '''
    def __init__(self, eventname: str) -> None:
        self.name = eventname.replace(" ","")

    def get_event(self):
        return self.name

    def __str__(self) -> str:
        return self.name

    def __eq__(self, __o: object) -> bool:
        return self.name == __o.name

class EventList:
    def __init__(self) -> None:
        self.list_of_events = []

    def __iter__(self):
        return EventIter(self)

    def add_event(self, event: Event) -> None:
        self.list_of_events.append(event)

    def __str__(self) -> str:
        return_str = ', '.join(map(str, self.list_of_events))
        return return_str


class EventIter:
    def __init__(self, eventlist: EventList) -> None:
        self._list_of_events = eventlist.list_of_events
        self._current_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._current_index < len(self._list_of_events):
            member = self._list_of_events[self._current_index]
            self._current_index += 1
            return member

        raise StopIteration
