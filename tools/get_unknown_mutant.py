#!/usr/bin/env python

import os
import sys
import json
import csv
import re
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

def _as_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _copy_selected_query(row):
    query_path = os.path.join(MARIPOSA_PATH, row["query_path"])
    shutil.copy(query_path, "./unknown_mutant.smt2")
    print(f"Copied {query_path} to current directory as unknown_mutant.smt2")


def _write_reseeded_mutant(row):
    seed = _as_int(row.get("command"))
    if seed is None:
        return False

    vanilla_rel = row.get("vanilla_path", "")
    vanilla_abs = os.path.join(MARIPOSA_PATH, vanilla_rel)
    if not os.path.isfile(vanilla_abs):
        return False

    with open(vanilla_abs, "r", encoding="utf-8") as f:
        text = f.read()

    seed_line = f"(set-option :smt.random_seed {seed})"
    pattern = r"^\(set-option\s+:smt\.random_seed\s+[^\)]+\)\s*$"
    updated_text, count = re.subn(pattern, seed_line, text, flags=re.MULTILINE)
    if count == 0:
        updated_text = seed_line + "\n" + text

    with open("./unknown_mutant.smt2", "w", encoding="utf-8") as f:
        f.write(updated_text)

    print(
        f"Created unknown_mutant.smt2 from {vanilla_abs} with :smt.random_seed {seed}"
    )
    return True


csv_path = "mariposa_res.csv"
if not os.path.isfile(csv_path):
    print("mariposa_res.csv is missing")
    sys.exit(1)

unknown_rows = []
with open(csv_path, "r", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if _as_int(row.get("result_code"), -1) == 4:
            unknown_rows.append(row)

if not unknown_rows:
    print("No unknown mutants found in mariposa_res.csv")
    sys.exit(1)

# Prefer unknown non-rename mutants with existing files.
selected_row = None
for row in unknown_rows:
    if row.get("perturbation") == "rename":
        continue
    query_path = os.path.join(MARIPOSA_PATH, row.get("query_path", ""))
    if os.path.isfile(query_path):
        selected_row = row
        break

# Fallback to any unknown mutant with an existing file.
if selected_row is None:
    for row in unknown_rows:
        query_path = os.path.join(MARIPOSA_PATH, row.get("query_path", ""))
        if os.path.isfile(query_path):
            selected_row = row
            break

if selected_row is not None:
    _copy_selected_query(selected_row)
    sys.exit(0)

# Final fallback: handle unknown reseed entries even when mutant files were not kept.
for row in unknown_rows:
    if row.get("perturbation") == "reseed" and _write_reseeded_mutant(row):
        sys.exit(0)

print("No usable unknown mutant found: files missing and no reseed fallback available")
sys.exit(1)
