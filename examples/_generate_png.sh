#!/bin/bash

for FILE in $(ls *.bao)
do
    echo $FILE
    python3 ../boxaro.py -i $FILE -o ${FILE%.bao}.gv
    dot -Tpng -o${FILE%.bao}.png ${FILE%.bao}.gv
done