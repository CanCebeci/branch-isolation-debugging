#!/bin/bash
WRAPPERS_DIR="$(dirname "$0")"

SMT_INPUT=$1
EXP=${2:-"default"}
SOLVER=${3:-"z3_4_13_0"}

$WRAPPERS_DIR/run_mariposa.sh $SMT_INPUT $EXP $SOLVER

grep $PROJ mariposa_res.csv | cut -d "," -f 8 > time.txt; python3 $WRAPPERS_DIR/plot.py $(basename $SMT_INPUT)
mv histogram.pdf $(basename $SMT_INPUT).histogram.pdf
cp time.txt $(basename $SMT_INPUT).time.txt
code $(basename $SMT_INPUT).histogram.pdf