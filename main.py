import time
from heuristicas import heuristica_limite_inferior, heuristica_v2
from plotar import plotar_grafo
from podas import atribuicao_parcial, checar_positivos_isolados, checar_vizinhos_afetados, \
        unico_fornecedor_de_dois, propagar_local, atribuicao_completa
from matriz import leitura_matriz_adjacencia

# Importação para vetores com mais de 1000 posições
import sys
sys.setrecursionlimit(1200)

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
    print("Tempo de execução: %.2f segundos"% (fim - inicio))

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

#arquivo = r"matrizes\johnson8-2-4.mtx" # 28*28 com 210 posições - mínimo 6
#arquivo = r"matrizes\johnson8-4-4.mtx" # 45*45 com 918 posições - mínimo 4
arquivo = r"matrizes\johnson8-4-4.mtx" # 70*70 com 1855 posições - mínimo 4
#arquivo = r"matrizes\c-fat200-2.mtx"  # 200*200 com 3235 posições - mínimo ? - passou mais de 1 hora e não terminou
#arquivo = r"matrizes\johnson16-2-4.mtx" # 120*120 com 5460 posições - mínimo ?
#arquivo = r"matrizes\C1000-9.mtx" # 1000 * 1000 com 450.079 posições - mínimo ?

calcular(leitura_matriz_adjacencia(arquivo))