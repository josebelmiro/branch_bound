"""
    Heurísticas
"""

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
    Sugestão de nova heurística
    A alteração é substituir a heurística atual por um lower bound que some a soma já atribuída com uma 
    estimativa mínima para “consertar” os vértices ainda não satisfeitos, usando o número de componentes 
    entre vértices que precisam de adjacência positiva e arredondando por cima metade desse total: 
    LB = soma_atribuida + ceil(R/2). A intuição é que cada nova atribuição positiva pode conectar pelo 
    menos dois desses vértices “carentes” ao formar uma aresta positiva, então cada componente do subgrafo 
    de carentes demanda pelo menos uma nova inserção positiva, e duas inserções podem resolver até dois 
    vértices de uma vez, justificando o ceil(R/2) como bound relaxado correto e barato de computar.​

    O que conta como “carente”
    Considere “carente de positividade” todo vértice v que, dado o estado atual, ainda precisa garantir 
    adjacência a um vértice com f∈{1,2}: isso inclui vértices já fixados com f∈{1,2} que ainda não têm 
    vizinho positivo certo, e vértices não atribuídos que não têm, por enquanto, vizinho positivo certo; 
    formar o subgrafo induzido por esses vértices e contar seus componentes dá R.​

    A parte “certo” usa os contadores: um v positivo está “satisfeito” se contador_vizinhos[v]+contador_vizinhos[v]>0; 
    se esse valor é 0, ele é carente; para v não atribuído, se não há nenhum vizinho já positivo, ele 
    ainda é carente de uma futura adjacência positiva, então entra no subgrafo de carentes até que se 
    garanta um vizinho positivo
"""
def heuristica_v2(atribuicoes, grafo, contador_vizinhos):
    n = len(grafo)
    soma = sum(x for x in atribuicoes if x != -1)

    # Conjunto de vértices que ainda exigem adjacência positiva (condição (ii) não garantida)
    carente = [False] * n
    for v in range(n):
        val = atribuicoes[v]
        pos_vizinhos = contador_vizinhos[v][1] + contador_vizinhos[v][2]
        if val in (1, 2):
            if pos_vizinhos == 0:
                carente[v] = True
        elif val == -1:
            if pos_vizinhos == 0:
                carente[v] = True
        # val==0: não conta para R (tratado por outro termo se desejar)

    # Conta componentes no subgrafo induzido por 'carente'
    visitado = [False] * n
    R = 0
    from collections import deque
    for v in range(n):
        if carente[v] and not visitado[v]:
            R += 1
            q = deque([v])
            visitado[v] = True
            while q:
                u = q.popleft()
                for w in grafo[u]:
                    if carente[w] and not visitado[w]:
                        visitado[w] = True
                        q.append(w)

    # ceil(R/2) = (R+1)//2
    return soma + (R + 1) // 2