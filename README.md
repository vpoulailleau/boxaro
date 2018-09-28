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
