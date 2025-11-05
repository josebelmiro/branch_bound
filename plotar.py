import matplotlib.pyplot as plt
"""
    Plota um grafo com o valor dos vértices e guarnições
"""
def plotar_grafo(grafo, atribuicoes, filename="grafo.png"):
    G = nx.Graph()
    n = len(grafo)
    G.add_nodes_from(range(n))

    for v in range(n):
        for u in grafo[v]:
            if not G.has_edge(v, u):
                G.add_edge(v, u)

    labels = {v: f"Vértice {v}\nGuarnição({atribuicoes[v]})" for v in range(n)}
    nx.draw(G, labels=labels, with_labels=True, node_color='lightblue', edge_color='gray', node_size=500)
    plt.savefig(filename)
    plt.show()