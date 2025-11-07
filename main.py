import time
import sys

from branchs_bounds import branch_bound_zeros, branch_bound

sys.setrecursionlimit(1200) # Importação para vetores com mais de 1000 posições

from auxiliares import inicializar_contadores, verifica_dominacao_romana_total
from plotar import plotar_grafo
from matriz import leitura_matriz_adjacencia

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
    #branch_bound(grafo, atribuicoes, 0, melhor_solucao, melhor_peso, logfile, contador_vizinhos)
    branch_bound_zeros(grafo, atribuicoes, 0, melhor_solucao, melhor_peso, logfile, contador_vizinhos)
    return melhor_solucao[0], melhor_peso[0]

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

#arquivo = r"matrizes\johnson8-2-4.mtx" # 28*28 com 210 posições - mínimo 6 - novo 9
#arquivo = r"matrizes\johnson8-4-4.mtx" # 45*45 com 918 posições - mínimo 4 - novo 13
#arquivo = r"matrizes\johnson8-4-4.mtx" # 70*70 com 1855 posições - mínimo 4 - novo 13
#arquivo = r"matrizes\c-fat200-2.mtx"  # 200*200 com 3235 posições - mínimo ? - novo 27
#arquivo = r"matrizes\johnson16-2-4.mtx" # 120*120 com 5460 posições - mínimo ? - novo 9
#arquivo = r"matrizes\C1000-9.mtx" # 1000 * 1000 com 450.079 posições - mínimo ? - novo 9
#arquivo = r"matrizes\C4000-5.mtx" # 4000 * 4000 com 4.000.268 posições - mínimo ? - novo 35
arquivo = r"matrizes\MANN-a81.mtx" # 3321 * 3321 com 5.506.380 posições - mínimo ? - novo 8


calcular(leitura_matriz_adjacencia(arquivo))