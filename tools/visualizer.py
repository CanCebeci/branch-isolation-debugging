import networkx as nx
from pyvis.network import Network

from datatypes import *

def color(p: Propagation):
    v = p.consequent_val
    if v == Val.TRUE:
        return "green"
    if v == Val.FALSE:
        return "red"
    if v == Val.NON_EVAL:
        return "yellow"
    
def intelligible_jst(jst):
    if jst == "bin":
        return "binary clause"
    if jst == "justification -1:":
        return "theory propagation"
    else:
        return jst

def qt_node_id(q):
    return f"QT:{q.qid}"

def term_node_id(t):
    return f"T:{t.sexpr}"

def cls_node_id(cls):
    return str([l.id for l in cls.lits])

def cls_level(cls):
    return max([p.distance for p in cls.props]) + 1

def visualize(props: list[Propagation], clauses: list[Clause], quantifiers: list[Quantifier], terms: list[Term]):
    G = nx.DiGraph()

    # Add propagation nodes
    for p in props:
        lit_id = p.consequent.id
        G.add_node(lit_id, label=f"{lit_id}\n({intelligible_jst(p.justification)})", title=p.consequent.sexpr, color=color(p), level=p.distance)
    
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