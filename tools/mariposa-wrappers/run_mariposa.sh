#!/bin/bash
WRAPPERS_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${MARIPOSA_PYTHON:-/usr/bin/python3.11}"

SMT_INPUT=$1
EXP=${2:-"default"}
SOLVER=${3:-"z3_4_13_0"}

SMT_INPUT_ABS=$(pwd)/$SMT_INPUT

pushd ~/mariposa
    PROJ=$($PYTHON_BIN src/exper_wizard.py single -i $SMT_INPUT_ABS -e $EXP -s $SOLVER --clear-existing | tee /dev/tty | grep "project dir" | awk '{print $NF}')
    echo "PROJ: $PROJ"

    if [ -z "$PROJ" ]; then
        echo "Failed to create project directory; exper_wizard.py did not return a project dir." >&2
        popd
        exit 1
    fi

    $WRAPPERS_DIR/get_csv.sh $PROJ $EXP $SOLVER true > mariposa_res.csv
popd

mv ~/mariposa/mariposa_res.csv .