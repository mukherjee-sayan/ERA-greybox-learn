# TLsep

## 1. File format.

The `tLsep` file format describes an Event-Recording Automaton (ERA), which is a strict subclass of Timed Automata (TA).
A file consists in a sequence of declarations in the following order:

- [event](#the-event-declaration)
- [location](#the-location-declaration)
- [transition](#the-transition-declaration)

**NOTE:** Unlike TA, we do not declare `clocks`, since here the clocks are implicit -- one clock per event.

## The `event` declaration 

```
event:id{attribute}
```
declares an event with an `id` and an `attribute`.
No other event shall have the same id.

### Supported event attributes

- `active`: an event is `active` only if the associated clock is active, 
**i.e.**, there exists at least one constraint on this event in the ERA.

 Otherwise, it should be left empty : {}

## The `location` declaration

```
location:id{attribute}
```
declares a location with an `id` and an `attribute`.
No two locations shall have the same id. 

### Supported location attributes
- `initial`: declares an `initial` location.
- `accepting`: declares an `accepting` location.

Otherwise, it should be left empty : {}

There should be exactly one location that is `initial`.
It is possible to have multiple `accepting` locations.
When declaring a location that is both initial and accepting, the attributes should be comma-separated, as follows:
    
```
location:id{initial,accepting}
```

## The `transition` declaration

```
transition:source:target:e:g
```
the above sentence declares a transition from location `source` to location `target` 
on event `e` and guard `g`.
The locations `source`, `target` and the event `e` should have been already declared.
The guard `g` is an [expression](#expressions) as defined below:

### Expressions

An `expression` is a conjunction of simple expressions.
A `simple expression` compares an event-clock with a **non-negative** integer.
Formally, expressions are formed using the following grammar:

```
expr ::= simple_expr 
         | simple_expr && expr

simple_expr ::= true_expr
                | clock_expr < int_expr
                | clock_expr > int_expr
                | clock_expr <= int_expr
                | clock_expr >= int_expr
                | clock_expr == int_expr
                
true_expr ::= True
int_expr ::= INTEGER
clock_expr ::= event_id
```

where `event_id` is an `id` of an event that has been already declared.

**NOTE:** The syntax of expressions defined above does not allow expressions like `2<a<3`, 
however, this can be written as follows: `a>2&&a<3` that has the same semantics as above.