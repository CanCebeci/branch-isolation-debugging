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

def visualize(props: list[Propagation]):
    G = nx.DiGraph()

    # Add nodes
    for p in props:
        lit_id = p.consequent.id
        G.add_node(lit_id, label=f"{lit_id}\n({intelligible_jst(p.justification)})", title=p.consequent.sexpr, color=color(p), level=p.distance)

    # # Add edges
    for p in props:
        cons_id = p.consequent.id
        for ant in p.antecedents:
            G.add_edge(ant.id, cons_id)

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