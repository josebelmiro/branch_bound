import time
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

"""
    Lê um arquivo no formato de matriz (.mtx) e retorna uma lista de adjacências
    Pressupõe:
        Grafo não dirigido
        Índices do arquivo começam em 1, sendo necessário ajustar para 0 na lista de adjacências
"""


def matriz_adjacencia(arquivo):
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


"""
    Teste de dominação romana total
"""


def verifica_dominacao_romana_total(grafo, atribuicoes):
    n = len(grafo)
    for v in range(n):
        # Solução incompleta
        if atribuicoes[v] == -1:
            print("Existe um vértice sem atribuição [0, 1, 2]")
            return False

        # Um vértice com uma guarnição deve ter pelo menos um vizinho com pelo menos uma guarnição
        if not any(atribuicoes[u] >= 1 for u in grafo[v]):
            print("Existe um vértice com uma guarnição ligado somente a vertices sem guarnições")
            return False

        # Se o vértice não tiver guarnição ele deve ter pelo menos um vizinho com duas guarnições
        if atribuicoes[v] == 0 and not any(atribuicoes[u] for u in grafo[v]):
            print("Existe um vértice sem guarnição que não está ligado a pel menos um vértice com duas guarnições")
            return False

        # Se o vértice tiver 1 ou 2 guarnições ele precisa ter pelo menos um vizinho com pelo menos uma guarnição
        if atribuicoes[v] in [1, 2] and not any(atribuicoes[u] >= 1 for u in grafo[v]):
            print(
                "Existe um vértice com guarnição [1, 2] que não está ligado a pelo menos um vértice com duas guarnições")
            return False

    print("As atribuições das guarnições satisfazem a dominação romana total")
    return True


"""
    Verifica se a atribuição completa é válida
"""


def atribuicao_completa(grafo, atribuicoes):
    n = len(grafo)
    for v in range(n):
        if atribuicoes[v] == -1:
            continue
        if atribuicoes[v] == 0:
            # Deve ter pelo menos um vizinho com f(u) = 2
            if not any(atribuicoes[u] == 2 for u in grafo[v]):
                return False
            # Deve ter pelo menos um vizinho com f(u) = 1 ou 2
            if not any(atribuicoes[u] in [1, 2] for u in grafo[v]):
                return False
        if atribuicoes[v] in [1, 2]:
            # Deve ter pelo menos um vizinho com f(u) = 1 ou 2
            if not any(atribuicoes[u] in [1, 2] for u in grafo[v]):
                return False
    return True


"""
    A heurística anterior somava soma_atribuida + vertices_nao_atribuídos
    Isso levava a um mínimo local (8), mas sem ela alcaçava (6)

    A heurística atual adiciona 1 se existir pelo menos um vértice não atribuído e consegue chegar a um mínimo global
    Caso não exista vértices não atribuídos ela devolve somente soma_atribuida
"""


def heuristica_limite_inferior(atribuicoes):
    soma_atribuida = sum(x for x in atribuicoes if x != -1)

    # Calcula quantos vértices não foram atribuídos
    vertices_nao_atribuídos = sum(1 for x in atribuicoes if x == -1)

    if vertices_nao_atribuídos >= 1:
        return soma_atribuida + 1
    return soma_atribuida


"""
    Branch and Bound recursivo
"""


def branch_bound(grafo, atribuicoes, vertice, melhor_solucao, melhor_peso, logfile, contador_vizinhos):
    n = len(grafo)

    if vertice == n:
        if atribuicao_completa(grafo, atribuicoes):
            peso = sum(atribuicoes)
            if peso < melhor_peso[0]:
                melhor_peso[0] = peso
                melhor_solucao[0] = atribuicoes[:]
        return

    for valor_guarnicao in [0, 1, 2]:
        # nova estratégia para verificar valores antigos
        valor_antigo = atribuicoes[vertice]

        atribuicoes[vertice] = valor_guarnicao

        # nova estratégia para verificar valores antigos
        atualizar_contadores(contador_vizinhos, grafo, vertice, valor_antigo, valor_guarnicao)

        if heuristica_limite_inferior(atribuicoes) >= melhor_peso[0]:
            # logfile.write(f"Poda por peso: peso atual {peso_atual} >= melhor peso {melhor_peso[0]}\n")

            # nova estratégia para verificar valores antigos
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        if not atribuicao_parcial_v2(contador_vizinhos, vertice, valor_guarnicao):
            # logfile.write(f"Poda por atribuição parcial inválida no vértice {vertice} com valor {valor_guarnicao}\n")

            # nova estratégia para verificar valores antigos
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        branch_bound(grafo, atribuicoes, vertice + 1, melhor_solucao, melhor_peso, logfile, contador_vizinhos)

        # nova estratégia para verificar valores antigos
        atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
        atribuicoes[vertice] = valor_antigo


"""
    Estas três funções tem uma estratégia de poda muito agresissa e encontra um mínimo local 12, mas o mínimo global é 6
    Elas tem a intenção de otimizar as verificações locais para reduzir o trabalho repetitivo, salvando resultados intermediários e evitar rechecagem
    O ganho de desempenho foi extremamente alto, ao invés de executar por mais de 1 minuto, executou instantaneamente
"""
"""
    Inicializa os contadores para cada vértice do grafo, armazenando quantos vizinhos de cada valor existem.
    Parâmetros:
    - grafo: lista de adjacências, onde cada índice representa um vértice e contém uma lista de seus vizinhos.
    Retorna:
    - lista de dicionários, um por vértice, com contadores para os valores [-1 (não atribuído), 0, 1, 2].
      Inicialmente, todos os vizinhos são considerados não atribuídos (-1).
    """


def inicializar_contadores(grafo):
    n = len(grafo)
    contador_vizinhos = [{0: 0, 1: 0, 2: 0, -1: len(grafo[v])} for v in range(n)]
    return contador_vizinhos


"""
    Atualiza incrementalmente os contadores dos vizinhos do vértice v quando seu valor é alterado de 'antigo' para 'novo'.

    Parâmetros:
    - contador_vizinhos: lista de dicionários com contadores por vértice.
    - grafo: lista de adjacências.
    - v: índice do vértice que teve seu valor alterado.
    - antigo: valor anterior atribuído ao vértice 'v'.
    - novo: novo valor atribuído ao vértice 'v'.

    Efeito:
    - Para cada vizinho u de v, decrementa o contador do valor antigo e incrementa o contador do novo valor,
      mantendo a contagem atualizada e permitindo validações rápidas no branch and bound.
    """


def atualizar_contadores(contador_vizinhos, grafo, v, antigo, novo):
    for u in grafo[v]:
        contador_vizinhos[u][antigo] -= 1
        contador_vizinhos[u][novo] += 1


"""
    Rápida validação parcial do vértice v com valor atribuído 'valor' usando os contadores incrementais.
    Essa função avalia se as restrições locais necessárias são satisfeitas para continuar a busca.

    Regras:
    - Se o valor é 0, o vértice deve ter pelo menos um vizinho com valor 2, ou vizinhos não atribuídos (-1),
      os quais ainda podem receber valores válidos no futuro.
    - Se o valor é 1 ou 2, o vértice deve ter pelo menos um vizinho com valor 1 ou 2, ou vizinhos não atribuídos.

    Parâmetros:
    - contador_vizinhos: lista de dicionários com contadores de vizinhos por valor.
    - v: índice do vértice a validar.
    - valor: valor atual atribuído ao vértice v.

    Retorna:
    - True se a validação parcial permite continuar a busca (restrições locais satisfeitas).
    - False caso contrário, para que o ramo seja podado.
    """


def atribuicao_parcial_v2(contador_vizinhos, v, valor):
    if valor == 0:
        # Permite passar se vizinhos ainda não atribuídos existem (-1)
        if contador_vizinhos[v][-1] > 0:
            return True
        return contador_vizinhos[v][2] > 0
    if valor in [1, 2]:
        if contador_vizinhos[v][-1] > 0:
            return True
        return (contador_vizinhos[v][1] + contador_vizinhos[v][2]) > 0
    return False


"""
    Verifica se a atribuição parcial é válida
"""


def atribuicao_parcial_v1(grafo, atribuicoes):
    n = len(grafo)
    for v in range(n):
        if atribuicoes[v] == -1:
            continue
        if atribuicoes[v] == 0:
            # Verifica apenas vizinhos atribuídos
            vizinhos_atribuidos = [atribuicoes[u] for u in grafo[v] if atribuicoes[u] != -1]

            if vizinhos_atribuidos:
                if 2 not in vizinhos_atribuidos:
                    # Se todos os vizinhos já foram atribuídos e nenhum é 2, falha
                    if all(atribuicoes[u] != -1 for u in grafo[v]):
                        return False
                if not any(x in [1, 2] for x in vizinhos_atribuidos):
                    if all(atribuicoes[u] != -1 for u in grafo[v]):
                        return False

        if atribuicoes[v] in [1, 2]:
            # Verifica apenas vizinhos atribuídos
            vizinhos_atribuidos = [atribuicoes[u] for u in grafo[v] if atribuicoes != -1]

            if vizinhos_atribuidos:
                if not any(x in [1, 2] for x in vizinhos_atribuidos):
                    if all(atribuicoes[u] != -1 for u in grafo[v]):
                        return False
    return True


"""
    Função de dominação romana total
"""


def dominacao_romana_total(grafo):
    contador_vizinhos = inicializar_contadores(grafo)
    logfile = ""

    n = len(grafo)
    atribuicoes = [-1] * n

    melhor_solucao = [None]
    melhor_peso = [float('inf')]
    branch_bound(grafo, atribuicoes, 0, melhor_solucao, melhor_peso, logfile, contador_vizinhos)
    return melhor_solucao[0], melhor_peso[0]


"""
    Função identica a anterior, mas com carregamento de arquivo para registro de log
    Essa segunda versão é para testar se o registro de log aumenta consideravelmente o tempo de execução
"""


def dominacao_romana_total_log(grafo):
    contador_vizinhos = inicializar_contadores(grafo)

    # Registro de log
    with open("log.txt", "w") as logfile:
        n = len(grafo)
        atribuicoes = [-1] * n

        melhor_solucao = [None]
        melhor_peso = [float('inf')]
        branch_bound(grafo, atribuicoes, 0, melhor_solucao, melhor_peso, logfile, contador_vizinhos)
        return melhor_solucao[0], melhor_peso[0]


def calcular(grafo):
    # Calcula o tempo de execução
    inicio = time.perf_counter()

    melhor_solucao, melhor_peso = dominacao_romana_total(grafo)
    if melhor_solucao is None:
        print("Nenhuma solução válida foi encontrada para esse grafo.")
    else:
        print("A melhor atribuição encontrado de f(v):", melhor_solucao)
        print("Peso mínimo:", melhor_peso)
        verifica_dominacao_romana_total(grafo, melhor_solucao)
        # plotar_grafo(grafo, melhor_solucao)

    # Calcula o tempo de execução
    fim = time.perf_counter()
    print(f"Tempo de execução: {fim - inicio} segundos")


arquivo = "johnson8-2-4.mtx"  # Arquivo na mesma pasta do projeto
calcular(matriz_adjacencia(arquivo))

"""
    A resposta para o arquivo johnson8-2-4.mtx com apenas 28 vértices foi
    Leitura concluída
    A melhor atribuição encontrado de f(v):  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0]
    Peso mínimo: 6
    As atribuições das guarnições satisfazem a dominação romana total

    O problema de Dominação Romana Total é combinatorial
    johnson8-2-4.mtx tem 28 vértices
    Como vértice pode assumir 3 valores [0, 1, 2] o espaço de busca para 3^28 possibilidades
"""