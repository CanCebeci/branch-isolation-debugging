#!/usr/bin/env python3

import os
import sys
import json
import subprocess

from config import *

SOLVER_TAG      = "z3_branch_isolation"
EXPER_TAG       = "default_keep_mutants"

def setup_mariposa():
    # Make sure Mariposa is installed where expected
    if not os.path.isdir(MARIPOSA_PATH):
        print(f"Expected Mariposa at {MARIPOSA_PATH}")
        sys.exit(1)

    # Make sure Mariposa can use the correct version of Z3
    with open(f"{MARIPOSA_PATH}/config/solvers.json", "r") as f:
        solvers = json.load(f)
    if SOLVER_TAG in solvers:
        print(f"Mariposa using {SOLVER_TAG} at {solvers[SOLVER_TAG]['path']}")
    else:
        print(f"Mariposa's solver config is missing {SOLVER_TAG}. Adding it at {Z3_BIN}")
        solvers[SOLVER_TAG] = {'path': Z3_BIN, 'date': '2024/01/25'}
        with open(f"{MARIPOSA_PATH}/config/solvers.json", "w") as f:
            json.dump(solvers, f, indent=4)

    # Make sure Mariposa can be configured to keep mutants
    with open(f"{MARIPOSA_PATH}/config/expers.json", "r") as f:
        expers = json.load(f)
    if not EXPER_TAG in expers:
        print(f"Adding {EXPER_TAG} to {MARIPOSA_PATH}/config/expers.json")
        expers[EXPER_TAG] = expers["default"].copy()
        expers[EXPER_TAG]["keep_mutants"] = True
        with open(f"{MARIPOSA_PATH}/config/expers.json", "w") as f:
            json.dump(expers, f, indent=4)


setup_mariposa()

smt_input=sys.argv[1]
experiment=EXPER_TAG
solver=SOLVER_TAG

subprocess.run([f"{TOOLS_DIR}/mariposa-wrappers/run_mariposa.sh", smt_input, experiment, solver], check=True)