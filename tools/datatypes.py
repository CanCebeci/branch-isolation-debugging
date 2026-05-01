from dataclasses import dataclass
from enum import Enum

@dataclass 
class Lit:
    id: int     # ID in the assigndump trace
    sexpr: str          # pretty printed expression

class Val(Enum):
    TRUE = 1
    FALSE = 2
    NON_EVAL = 3        # The value of expressions that are not fully evaluable in the failing branch

@dataclass 
class Propagation:
    consequent: Lit
    antecedents: list[Lit]
    justification: str
    consequent_val: Val       # Does the failing branch make this propagation (or a get-value-equivalent one)?
    input: bool         # Is this an input assertion, or does it result from rewriting an input assertion?
    distance: int       # The number of propagations to get to false

@dataclass 
class Clause:
    lits: list[Lit]
    instance_hash: str
    props: list[Propagation]

@dataclass 
class Quantifier:
    qid: str
    bool_id: int  # The bool_var id in the unknown mutant of the source quantifier
    clauses_created: list[Clause]

