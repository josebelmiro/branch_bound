from collections import defaultdict

"""
    Lê um arquivo no formato de matriz (.mtx) e retorna uma lista de adjacências
    Pressupõe:
        Grafo não dirigido
        Índices do arquivo começam em 1, sendo necessário ajustar para 0 na lista de adjacências
"""
def leitura_matriz_adjacencia(arquivo):
    adjacencias = defaultdict(list)
    with open(arquivo, "r") as file:
        for linha in file:
            linha = linha.strip()

            # Ignora cabeçalhos e linhas em branco
            if linha.startswith("%") or linha == '':
                continue

            parte = linha.split()

            if len(parte) < 2:
                continue

            # conversão para índices de base zero
            i, j = int(parte[0]) - 1, int(parte[1]) - 1

            # ignora o auto loop
            if i != j:
                adjacencias[i].append(j)
                adjacencias[j].append(i)

    # Cria uma lista de adjacências para todos os vétices presentes
    n = max(adjacencias) + 1

    grafo = [adjacencias[i] for i in range(n)]

    # O objetivo é ordenar o grafo pelos vértices com maior número de arestas
    # Como eles tem maior impacto na construção da solução, eles podem impor mais restrições

    # Ordenar vértices pelo grau decrescente
    ordem = sorted(range(n), key=lambda x: len(grafo[x]), reverse=True)

    # Cria um mapeamento antigo índice -> novo índice
    mapeamento = {antigo: novo for novo, antigo in enumerate(ordem)}

    # Reorganiza a lista de adjacência com base na nova ordem e atualiza os vizinhos
    grafo_ordenado = []
    for i in ordem:
        novos_vizinhos = [mapeamento[v] for v in grafo[i]]
        grafo_ordenado.append(novos_vizinhos)

    print("Leitura concluída")
    return grafo_ordenado
