# boxaro

Easy graphs with boxes and arrows. Bored with long diagram edition (initial layout nightmare, difficulty to add element without breaking the layout), this project is for you.

boxaro is boxes + arrows.

boxaro is licenced under 3-clause BSD licence

# Usage

* You describe your graph with an easy textual syntax
* boxaro convert your textual description in a graphviz compatible syntax
* graphviz (dot, neato…) generates PNG, SVG…

# Example

```
box my_first_box
    inputs
        A
        B
    outputs
        C
        D
        
    box another_box
        label A nice box
    
connections
    my_first_box.A -> my_first_box.another_box
    my_first_box.B -> my_first_box.another_box
    my_first_box.another_box -> my_first_box.C
    my_first_box.another_box "important message"-> my_first_box.C
```

# Syntax

* indentation is important (readibility counts)
* it is suggested to use 4-space indentation

## Box

A box is created by issuing a
```
box my_first_box
```
where `my_first_box` is an identifier made of letters, numbers and underscores.

A box may contain another box.

A box may have inputs:
```
box my_first_box
    inputs
        A
        B
```

A box may have outputs:
```
box my_first_box
    outputs
        C
        D
```

A box may have a label that is not its identifer:
```
box my_first_box
    label A nice text
```

## Connections

The list of connections is provided in a `connections` section. Each connection mentions the full paths to elements:
```
connections
    my_first_box.A -> my_first_box.another_box
    my_first_box.another_box -> my_first_box.C
```

The arrow of a connection may be labeled:
```
connections
    my_first_box.another_box "important message"-> my_first_box.C
```
