import os

MARIPOSA_PATH   = os.path.expanduser("~/mariposa")
TOOLS_DIR      = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT       = TOOLS_DIR + "/.."
Z3_DIR          = REPO_ROOT + "/z3"
Z3_BIN          = Z3_DIR + "/build/z3"