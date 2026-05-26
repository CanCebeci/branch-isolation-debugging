import networkx as nx
from pyvis.network import Network

from datatypes import *
from utils import intelligible_jst


def _format_val(v: Val | None):
    if v is None:
        return "UNKNOWN"
    return v.name


def _format_lit(l: Lit):
    return f"{l.id}: {l.sexpr}"


def _print_text_summary(
    props: list[Propagation],
    clauses: list[Clause],
    quantifiers: list[Quantifier],
    terms: list[Term],
):
    print("=== Relevant Propagations ===")
    if not props:
        print("(none)")
    for i, p in enumerate(props, start=1):
        ant_ids = [a.id for a in p.antecedents]
        print(
            f"[{i}] level={p.distance} val={_format_val(p.consequent_val)} "
            f"jst={p.justification or '-'} consequent=({_format_lit(p.consequent)}) "
            f"antecedents={ant_ids} "
            f"input={p.input}"
        )

    print("\n=== Relevant Clauses ===")
    if not clauses:
        print("(none)")
    for i, cls in enumerate(clauses, start=1):
        lit_ids = [l.id for l in cls.lits]
        prop_cons = [p.consequent.id for p in cls.props]
        print(
            f"[{i}] instance_hash={cls.instance_hash} lits={lit_ids} "
            f"used_by_props={prop_cons}"
        )

    print("\n=== Relevant Quantifiers ===")
    if not quantifiers:
        print("(none)")
    for i, q in enumerate(quantifiers, start=1):
        clause_ids = [cls_node_id(c) for c in q.clauses_created]
        print(f"[{i}] qid={q.qid} bool_id={q.bool_id} clauses={clause_ids}")

    print("\n=== Relevant Terms ===")
    if not terms:
        print("(none)")
    for i, t in enumerate(terms, start=1):
        clause_ids = [cls_node_id(c) for c in t.clauses_created]
        print(f"[{i}] sexpr={t.sexpr} clauses={clause_ids}")

def color(p: Propagation):
    v = p.consequent_val
    if v == Val.TRUE:
        return "green"
    if v == Val.FALSE:
        return "red"
    if v == Val.NON_EVAL:
        return "yellow"

def qt_node_id(q):
    return f"QT:{q.qid}"

def term_node_id(t):
    return f"T:{t.sexpr}"

def cls_node_id(cls):
    return str([l.id for l in cls.lits])

def cls_level(cls):
    return max([p.distance for p in cls.props]) + 1

def visualize(props: list[Propagation], clauses: list[Clause], quantifiers: list[Quantifier], terms: list[Term]):
    _print_text_summary(props, clauses, quantifiers, terms)

    G = nx.DiGraph()

    # Add propagation nodes
    for p in props:
        lit_id = p.consequent.id
        G.add_node(lit_id, label=f"{lit_id}\n({intelligible_jst(p)})", title=p.consequent.sexpr, color=color(p), level=p.distance)
    
    for p in props:
        cons_id = p.consequent.id
        for ant in p.antecedents:
            G.add_edge(ant.id, cons_id)

    for cls in clauses:
        node_id = cls_node_id(cls)
        G.add_node(node_id, label=f"{node_id}\n({cls.instance_hash})", title="", color="gray", shape="hexagon", level=cls_level(cls))
        for p in cls.props:
            G.add_edge(node_id, p.consequent.id)

    for q in quantifiers:
        G.add_node(qt_node_id(q), label=q.qid, title="", color="gray", shape="diamond", level=max([cls_level(cls) for cls in q.clauses_created]) + 1)
        for cls in q.clauses_created:
            G.add_edge(qt_node_id(q), cls_node_id(cls))

    for t in terms:
        G.add_node(term_node_id(t), label=t.sexpr, title="", color="gray", shape="box", level=max([cls_level(cls) for cls in t.clauses_created]) + 1)
        for cls in t.clauses_created:
            G.add_edge(term_node_id(t), cls_node_id(cls))

    # Create interactive network
    net = Network(height="600px", width="100%", directed=True)

    net.set_options("""
{
  "layout": {
    "hierarchical": {
      "enabled": true,
      "direction": "DU"
    }
  },
  "physics": {
    "enabled": false
  }
}
""")

    net.from_nx(G)

    # Generate HTML
    net.write_html("propagation_tree.html")