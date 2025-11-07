"""
    Branch and Bound recursivo
    Aqui são chamadas as funções de podas
"""
from auxiliares import atualizar_contadores
from heuristicas import heuristica_limite_inferior
from podas import propagar_local, checar_positivos_isolados, unico_fornecedor_de_dois, checar_vizinhos_afetados, \
    atribuicao_parcial, atribuicao_completa


def branch_bound(grafo, atribuicoes, vertice, melhor_solucao, melhor_peso, logfile, contador_vizinhos):
    n = len(grafo)

    # Caso base: último vértice
    if vertice == n:
        if atribuicao_completa(grafo, atribuicoes):
            peso = sum(atribuicoes)
            if peso < melhor_peso[0]:
                melhor_peso[0] = peso
                melhor_solucao[0] = atribuicoes[:]
        return

    # A alteração [0, 1, 2] -> [2, 1, 0] deu uma queda drástica de processamento no arquivo
    # Provalvemente porque impõe restrições muito mais rápidas
    for valor_guarnicao in [2, 1, 0]:
        valor_antigo = atribuicoes[vertice]

        atribuicoes[vertice] = valor_guarnicao
        atualizar_contadores(contador_vizinhos, grafo, vertice, valor_antigo, valor_guarnicao)

        # 1) Poda por limite inferior
        # Heurística é mais custosa if heuristica_v2(atribuicoes, grafo, contador_vizinhos) >= melhor_peso[0]:
        if heuristica_limite_inferior(atribuicoes) >= melhor_peso[0]:
            #logfile.write(f"Poda por peso: peso atual {peso_atual} >= melhor peso {melhor_peso[0]}\n")

            # nova estratégia para verificar valores antigos
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        # 2) Checagem local do próprio vértice (regra parcial TRD)
        if not atribuicao_parcial(contador_vizinhos, vertice, valor_guarnicao):
            #logfile.write(f"Poda por atribuição parcial inválida no vértice {vertice} com valor {valor_guarnicao}\n")

            # nova estratégia para verificar valores antigos
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        # 3) Forward-checking: checar inviabilidade imediata nos vizinhos afetados
        if not checar_vizinhos_afetados(contador_vizinhos, grafo, vertice, atribuicoes):
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        # 4) Único fornecedor de 2
        if not unico_fornecedor_de_dois(contador_vizinhos, grafo, vertice, atribuicoes):
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        # 5) Regra de poda por par impossível para positivos (reforçada)
        if not checar_positivos_isolados(grafo, atribuicoes, contador_vizinhos, vertice):
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        # 6) Propagação em k níveis
        # k = 0, não executa
        # k = 1, já é executado em checar_vizinhos_afetados
        if not propagar_local(contador_vizinhos, grafo, [vertice], atribuicoes, 0):
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        branch_bound(grafo, atribuicoes, vertice + 1, melhor_solucao, melhor_peso, logfile, contador_vizinhos)

        atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
        atribuicoes[vertice] = valor_antigo

def branch_bound_zeros(grafo, atribuicoes, vertice, melhor_solucao, melhor_peso, logfile,
                                    contador_vizinhos):
    n = len(grafo)

    # Caso base: todos vértices atribuídos
    if vertice == n:
        if atribuicao_completa(grafo, atribuicoes):
            peso = sum(atribuicoes)
            if peso < melhor_peso[0]:
                melhor_peso[0] = peso
                melhor_solucao[0] = atribuicoes[:]
        return

    # Se vértice já atribuído, tenta explorar vizinhos livres primeiro
    if atribuicoes[vertice] != -1:
        vizinhos_livres = [v for v in grafo[vertice] if atribuicoes[v] == -1]

        if vizinhos_livres:
            # Vizinho livre com maior grau recebe 1
            v_maior_grau = max(vizinhos_livres, key=lambda x: len(grafo[x]))
            valor_antigo_v = atribuicoes[v_maior_grau]
            atribuicoes[v_maior_grau] = 1
            atualizar_contadores(contador_vizinhos, grafo, v_maior_grau, 1, valor_antigo_v)

            # Outros vizinhos livres recebem 0
            outros_vizinhos = [v for v in vizinhos_livres if v != v_maior_grau]
            for v in outros_vizinhos:
                v_antigo = atribuicoes[v]
                atribuicoes[v] = 0
                atualizar_contadores(contador_vizinhos, grafo, v, 0, v_antigo)

            # Cálculo do limite inferior para poda
            limite_inferior = heuristica_limite_inferior(atribuicoes)
            # Poda se a estimativa ultrapassa melhor peso encontrado
            if atribuicao_parcial(contador_vizinhos, vertice, 2) and limite_inferior <= melhor_peso[0]:
                proximo = next((i for i, val in enumerate(atribuicoes) if val == -1), None)
                if proximo is not None:
                    branch_bound_zeros_backtracking(grafo, atribuicoes, proximo, melhor_solucao, melhor_peso, logfile,
                                                    contador_vizinhos)
                else:
                    if atribuicao_completa(grafo, atribuicoes):
                        peso = sum(atribuicoes)
                        if peso < melhor_peso[0]:
                            melhor_peso[0] = peso
                            melhor_solucao[0] = atribuicoes[:]

            # Retrocesso das atribuições nos vizinhos
            for v in outros_vizinhos:
                atualizar_contadores(contador_vizinhos, grafo, v, -1, 0)
                atribuicoes[v] = -1

            atualizar_contadores(contador_vizinhos, grafo, v_maior_grau, -1, 1)
            atribuicoes[v_maior_grau] = -1
        else:
            # Se não há vizinhos livres, avança para próximo vértice não atribuído
            proximo = next((i for i, val in enumerate(atribuicoes) if val == -1), None)
            if proximo is not None:
                branch_bound_zeros_backtracking(grafo, atribuicoes, proximo, melhor_solucao, melhor_peso, logfile,
                                                contador_vizinhos)
        return

    # Vértice não atribuído: tenta atribuir 2
    valor_antigo_vertice = atribuicoes[vertice]
    atribuicoes[vertice] = 2
    atualizar_contadores(contador_vizinhos, grafo, vertice, 2, valor_antigo_vertice)

    # Processa vizinhos livres para atribuições
    vizinhos_livres = [v for v in grafo[vertice] if atribuicoes[v] == -1]

    if vizinhos_livres:
        # Vizinho livre com maior grau recebe 1
        v_maior_grau = max(vizinhos_livres, key=lambda x: len(grafo[x]))
        valor_antigo_v = atribuicoes[v_maior_grau]
        atribuicoes[v_maior_grau] = 1
        atualizar_contadores(contador_vizinhos, grafo, v_maior_grau, 1, valor_antigo_v)

        # Outros vizinhos livres recebem 0
        outros_vizinhos = [v for v in vizinhos_livres if v != v_maior_grau]
        for v in outros_vizinhos:
            v_antigo = atribuicoes[v]
            atribuicoes[v] = 0
            atualizar_contadores(contador_vizinhos, grafo, v, 0, v_antigo)
    else:
        outros_vizinhos = []

    # Calcúlo do limite inferior para poda antes da recursão
    limite_inferior = heuristica_limite_inferior(atribuicoes)

    # Validação parcial combinada com poda
    if atribuicao_parcial(contador_vizinhos, vertice, 2) and limite_inferior <= melhor_peso[0]:
        proximo = next((i for i, val in enumerate(atribuicoes) if val == -1), None)
        if proximo is not None:
            branch_bound_zeros(grafo, atribuicoes, proximo, melhor_solucao, melhor_peso, logfile,
                                            contador_vizinhos)
        else:
            if atribuicao_completa(grafo, atribuicoes):
                peso = sum(atribuicoes)
                if peso < melhor_peso[0]:
                    melhor_peso[0] = peso
                    melhor_solucao[0] = atribuicoes[:]

    # Retrocesso: desfaz atribuições dos vizinhos
    for v in outros_vizinhos:
        atualizar_contadores(contador_vizinhos, grafo, v, -1, 0)
        atribuicoes[v] = -1

    if vizinhos_livres:
        atualizar_contadores(contador_vizinhos, grafo, v_maior_grau, -1, 1)
        atribuicoes[v_maior_grau] = -1

    # Retrocesso: desfaz atribuição do vértice atual
    atualizar_contadores(contador_vizinhos, grafo, vertice, valor_antigo_vertice, 2)
    atribuicoes[vertice] = valor_antigo_vertice