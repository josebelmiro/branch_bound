"""
    Estas três funções tem uma estratégia de poda muito agressiva e encontra um mínimo local 12, mas o mínimo global é 6
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
    contador_vizinhos = [ {0:0, 1:0, 2:0, -1:len(grafo[v])} for v in range(n)]
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
    Função para verificar se a solução proposta satisfaz os requisitos
    Teste de dominação romana total
"""
def verifica_dominacao_romana_total(grafo, atribuicoes):
    n = len(grafo)
    for v in range(n):
        # Solução incompleta
        if atribuicoes[v] == -1:
            print ("Existe um vértice sem atribuição [0, 1, 2]")
            return False

        # Um vértice com uma guarnição deve ter pelo menos um vizinho com pelo menos uma guarnição
        if not any(atribuicoes[u] >= 1 for u in grafo[v]):
            print("Existe um vértice com uma guarnição ligado somente a vertices sem guarnições")
            return False

        # Se o vértice não tiver guarnição ele deve ter pelo menos um vizinho com duas guarnições
        # Correção (05.11.25): atribuicoes[u] -> atribuicoes[u] == 2
        if atribuicoes[v] == 0 and not any(atribuicoes[u] == 2 for u in grafo[v]):
            print("Existe um vértice sem guarnição que não está ligado a pel menos um vértice com duas guarnições")
            return False

        # Se o vértice tiver 1 ou 2 guarnições ele precisa ter pelo menos um vizinho com pelo menos uma guarnição
        if atribuicoes[v] in [1, 2] and not any(atribuicoes[u] >= 1 for u in grafo[v]):
            print("Existe um vértice com guarnição [1, 2] que não está ligado a pelo menos um vértice com guarnições")
            return False

    print("As atribuições das guarnições satisfazem a dominação romana total")
    return True

"""
    Inicialização da função de dominação romana total
    Utilizada para construir log
    Foi separada porque aumenta o custo durante os testes
"""
"""
def dominacao_romana_total_com_log(grafo):
    contador_vizinhos = inicializar_contadores(grafo)

    # Registro de log
    with open("log.txt", "w") as logfile:
        n = len(grafo)
        atribuicoes = [-1] * n

        melhor_solucao = [None]
        melhor_peso = [float('inf')]
        branch_bound(grafo, atribuicoes, 0, melhor_solucao, melhor_peso, logfile, contador_vizinhos)
        return melhor_solucao[0], melhor_peso[0]
"""