#!/usr/bin/env python

import os
import sys
import json
import csv
import subprocess
import shutil

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

# Find a row with result_code == 4 and perturbation != 'rename'
csv_path = "mariposa_res.csv"
if os.path.isfile(csv_path):
    selected_row = None
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["result_code"]) != 4 or row["perturbation"] == "rename":
                continue

            query_path = os.path.join(MARIPOSA_PATH, row["query_path"])
            if os.path.isfile(query_path):
                selected_row = row
                break

    if selected_row is None:
        print("No existing unknown non-rename mutant found in mariposa_res.csv")
        sys.exit(1)

    query_path = os.path.join(MARIPOSA_PATH, selected_row["query_path"])
    shutil.copy(query_path, "./unknown_mutant.smt2")
    print(f"Copied {query_path} to current directory as unknown_mutant.smt2")
