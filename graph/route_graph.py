import networkx as nx

def build_graph(routes):
    G = nx.DiGraph()

    for route in routes:
        for leg in route["trechos"]:
            G.add_edge(
                leg["origem"],
                leg["destino"],
                modal=leg["modal"],
                custo=1,  # placeholder
                tempo=1   # placeholder
            )

    return G
