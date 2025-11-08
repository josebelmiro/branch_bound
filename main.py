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

    """
        Aqui eu defino qual função utilizar, B&B ou guloso
    """
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

# Arquivos em ordem pelo tamanho do arquivo
# Arquivos com V=1000 impõe recursão de V e deixa a máquina bem lenta em razão da profundidade
# Considere mínimo a primeira função.
#   Se tiver ? é porque não terminou de rodar
#   Se for observado que o número baixou muito eu colocarei o valor

arquivo = r"matrizes\johnson8-2-4.mtx" # V=28 A=210 - Pesos: mínimo 6 - guloso 9 - gemini ?
#arquivo = r"matrizes\hamming6-4.mtx" # V=64 A=704 - Pesos: mínimo ? (parei em 8) - guloso 24 - gemini 4 - piorou pra 6
#arquivo = r"matrizes\MANN-a9.mtx" # V=45 A=918 - Pesos: mínimo 4 - guloso 8 - gemini ?
#arquivo = r"matrizes\johnson8-4-4.mtx" # V=70 A=1855 - Pesos: mínimo 4 - guloso 13 - gemini ?
#arquivo = r"matrizes\c-fat200-2.mtx" # V=200 A=3235 - Pesos: mínimo ? (parei em 113) - guloso 27 - gemini ?
#arquivo = r"matrizes\johnson16-2-4.mtx" # V=120 A=5460 - Pesos: mínimo ? (parei em 7) - guloso 9 - gemini ?
#arquivo = r"matrizes\C1000-9.mtx" # V=1000 A=450.079 - Pesos: mínimo ? - guloso 9 - gemini ?


calcular(leitura_matriz_adjacencia(arquivo))