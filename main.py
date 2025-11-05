import time
from heuristicas import heuristica_limite_inferior, heuristica_v2
from podas import atribuicao_parcial_v2, positivo_tem_par_possivel, checar_positivos_isolados_reforcado, \
    checar_vizinhos_afetados, checagens_incrementais_basicas, unico_fornecedor_de_dois, propagar_local, \
    atribuicao_parcial_v1, atribuicao_completa
from plotar import plotar_grafo
from matriz import leitura_matriz_adjacencia

"""
    Função para inicializar as operações
    Separada por fins pedagógicos
"""
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
        #plotar_grafo(grafo, melhor_solucao)

    # Calcula o tempo de execução
    fim = time.perf_counter()
    print(f"Tempo de execução: {fim - inicio} segundos")

"""
    Inicialização da função de dominação romana total
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
    Inicialização da função de dominação romana total
    Utilizada para construir log
    Foi separada porque aumenta o custo durante os testes
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
    Branch and Bound recursivo
    Aqui são chamadas as funções de podas
"""
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
        if not atribuicao_parcial_v2(contador_vizinhos, vertice, valor_guarnicao):
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

        # 4) Regra de poda por par impossível para positivos (reforçada)
        if not checar_positivos_isolados_reforcado(grafo, atribuicoes, contador_vizinhos, vertice):
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        """
        # Regras adicionais para poda mais agressiva
        # Aumentam consideravelmente o tempo de execução
        # johnson16-2-4.mtx # 120*120 com 5460 posições
        #   Ainda não conseguiram executar abaixo de 10 minutos (ainda nem sei quanto tempo leva)
        
        # Função nova (05.11.25): aumentou significativamente o custo de processamento
        # 4) Propagação leve (opcional): BFS rasa para capturar efeitos em cadeia baratos
        if not propagar_local(contador_vizinhos, grafo, [vertice], atribuicoes):
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue
            
        # Regras A e B incrementais
        if not checagens_incrementais_basicas(contador_vizinhos, grafo, atribuicoes, vertice):
            atribuicoes[vertice] = valor_antigo
            continue

        ok, unico = unico_fornecedor_de_dois(contador_vizinhos, grafo, atribuicoes, vertice)
        if not ok:
            # poda
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue

        # Política leve: não force atribuição; apenas use como restrição de valor:
        # Se estamos escolhendo valor para 'v' e v é o único fornecedor de 2 para algum w,
        # então só permita valor==2; caso contrário, podar esse valor.
        if unico is not None and vertice == unico and valor_guarnicao != 2:
            atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
            atribuicoes[vertice] = valor_antigo
            continue
        # Regras adicionais para poda a fim de aumentar a agressividade
        # Aumentou o tempo de execução
        """

        branch_bound(grafo, atribuicoes, vertice + 1, melhor_solucao, melhor_peso, logfile, contador_vizinhos)

        # nova estratégia para verificar valores antigos
        atualizar_contadores(contador_vizinhos, grafo, vertice, valor_guarnicao, valor_antigo)
        atribuicoes[vertice] = valor_antigo

arquivo = r"matrizes\johnson8-2-4.mtx" # 28*28 com 210 posições - < 2s h1 e < 6s h2
#arquivo = r"matrizes\johnson8-4-4.mtx" # 70*70 com 1855 posições - < 4s h1 e < 246s h2
#arquivo = r"matrizes\johnson16-2-4.mtx" # 120*120 com 5460 posições - mais que 15 minutos (não esperei) h1 e mais que 20 minutos (não esperei) h2
calcular(leitura_matriz_adjacencia(arquivo))

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