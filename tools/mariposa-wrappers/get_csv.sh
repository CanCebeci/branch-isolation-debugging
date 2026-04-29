#!/bin/bash

PROJ=$1
EXP=$2
SOLVER=$3 

SINGLE=${4:-true}

if [ "$SINGLE" != "true" ]; then
    sqlite3 -header -csv data/dbs/${PROJ:11}/$EXP.db "SELECT query_path, vanilla_path, perturbation,command,std_out ,std_error ,result_code ,elapsed_milli , check_sat_id ,timestamp FROM "${PROJ:11:-8}"_base_z3_"$SOLVER"_exp"

else
    sqlite3 -header -csv $PROJ/$EXP.db "SELECT query_path, vanilla_path, perturbation,command,std_out ,std_error ,result_code ,elapsed_milli , check_sat_id ,timestamp FROM "${PROJ:10}"_base_z3_"$SOLVER"_exp"
fi


