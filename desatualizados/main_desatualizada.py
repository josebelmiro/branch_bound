import time
import sys
from collections import deque, defaultdict
import matplotlib.pyplot as plt
import networkx as nx

sys.setrecursionlimit(1200) # Importação para vetores com mais de 1000 posições

"""
    Plota um grafo com o valor dos vértices e guarnições
"""
def plotar_grafo(grafo, atribuicoes, filename=r"imagens210\grafo.png"):
    G = nx.Graph()
    n = len(grafo)
    G.add_nodes_from(range(n))

    for v in range(n):
        for u in grafo[v]:
            if not G.has_edge(v, u):
                G.add_edge(v, u)

    # Mostra apenas labels 1 ou 2
    labels = {
        v: f"Vértice {v}\nGuarnição({atribuicoes[v]})"
        for v in range(n)
        if atribuicoes[v] == 1 or atribuicoes[v] == 2
    }

    # mostra todos os labels
    #labels =  {v: f"Vértice {v}\nGuarnição({atribuicoes[v]})" for v in range(n)}

    nx.draw(G, labels=labels, with_labels=True, node_color='lightblue', edge_color='gray', node_size=500)
    plt.savefig(filename)
    plt.show()

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
    Funções de podas
    Aumenta o custo operacional consideravelmente
"""

"""
    Retorna True se v (com f(v) em {1,2}) tem pelo menos um vizinho que pode (realisticamente) ser positivo,
    seja já positivo, seja não atribuído mas sem inviabilidade local se vier a ser 1 ou 2.
"""


def positivo_tem_par_possivel(grafo, atribuicoes, contador_vizinhos, vertice):
    # já tem vizinho positivo certo?
    if (contador_vizinhos[vertice][1] + contador_vizinhos[vertice][2]) > 0:
        return True

    # caso contrário, examinar vizinhos não atribuídos
    for u in grafo[vertice]:
        if atribuicoes[u] != -1:
            continue
        # Verificar se u poderia ser 1 ou 2 sem inviabilizar imediatamente:
        # - Se u=1: u precisará de algum vizinho positivo (v conta se v é positivo),
        #   então se v já é positivo, u=1 é viável localmente desde que v continue positivo.
        # - Se u=2: não há impedimento local imediato; 2 sempre fornece positividade.
        # Portanto, a mera existência de v positivo já torna u=1 viável localmente;
        # e u=2 é localmente aceitável em geral.
        return True

    # Não há positivos certos e não há vizinhos não atribuídos que sirvam de candidato imediato
    return False


"""
    Checa o próprio v (se positivo) e vizinhos positivos de v
    Poda se algum ficar sem par possível.
"""


def checar_positivos_isolados(grafo, atribuicoes, contador_vizinhos, vertice):
    # lista de candidatos a checar: v e vizinhos
    candidatos = [vertice]
    candidatos.extend(grafo[vertice])

    for x in candidatos:
        val = atribuicoes[x]
        if val in (1, 2):
            # Regra fortalecida: precisa de um par positivo possível
            if not positivo_tem_par_possivel(grafo, atribuicoes, contador_vizinhos, x):
                return False
    return True


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


def atribuicao_parcial(contador_vizinhos, vertice, valor):
    if valor == 0:
        # Permite passar se vizinhos ainda não atribuídos existem (-1)
        if contador_vizinhos[vertice][-1] > 0:
            return True
        return contador_vizinhos[vertice][2] > 0
    if valor in [1, 2]:
        if contador_vizinhos[vertice][-1] > 0:
            return True
        return (contador_vizinhos[vertice][1] + contador_vizinhos[vertice][2]) > 0
    return False


"""
    Essa função verifica se atribuição atual:
    Afeta as próximas atribuições
    Afeta as atribuições anteriores
    Caso tenha afetado negativamente é feita uma poda
"""


def checar_vizinhos_afetados(contador_vizinhos, grafo, vertice, atribuicoes):
    # checa inviabilidade em cada u vizinho de v
    for u in grafo[vertice]:
        val_u = atribuicoes[u]
        if val_u == -1:
            # ainda não atribuído: não podar aqui
            continue
        # regra TRD para u=0
        if val_u == 0:
            # se não há vizinho 2 e não há vizinho pendente (-1) que possa virar 2, inviável
            if contador_vizinhos[u][2] == 0 and contador_vizinhos[u][-1] == 0:
                return False
        # regra TRD para u positivo
        elif val_u in (1, 2):
            # se não há vizinho positivo e não há vizinho pendente (-1) que possa virar positivo, inviável
            if (contador_vizinhos[u][1] + contador_vizinhos[u][2]) == 0 and contador_vizinhos[u][-1] == 0:
                return False
    return True


"""
    Propagação iterativa

    Tem por objetivo localizar problemas futuros
    O próximo nível é executado por checar_vizinhos_afetados.
    Esta função só tem sentido se quiser explorar a partir do segundo nível

    Aumenta significativamente o custo de processamento

    É uma forma leve de “forward checking”/propagação de restrições típica em CSPs: 
    ao fixar v, não só verifica v, mas também N(v) e, opcionalmente, se propaga um 
    pouco além para capturar efeitos em cadeia baratos, tudo com custo linear no número 
    de arestas visitadas.

    Não decide novos valores automaticamente; apenas detecta impossibilidade antecipada 
    usando informações locais e contadores incrementais já mantidos, o que evita explorar
    subárvores inteiras que inevitavelmente falhariam adiante

    Caso essa tipo de poda seja rara, o custo operacional acaba sendo muito custoso
    Situação agravada em uma árvore de busca muito densa
"""


def propagar_local(contador_vizinhos, grafo, start_vertices, atribuicoes, k):
    fila = deque(start_vertices)
    visitado = set(start_vertices)
    # Isso evita realizar a verificação do próximo nível (1), pois já foi realizado em checar_vizinhos_afetados
    nivel = 1

    # processa nível 0 (opcional: checar os starts)
    while fila and nivel <= k:
        for _ in range(len(fila)):
            v = fila.popleft()
            val_v = atribuicoes[v]
            if val_v != -1:
                cont_v = contador_vizinhos[v]
                if val_v == 0:
                    if cont_v.get(2, 0) == 0 and cont_v.get(-1, 0) == 0:
                        return False
                elif val_v in (1, 2):
                    if (cont_v.get(1, 0) + cont_v.get(2, 0)) == 0 and cont_v.get(-1, 0) == 0:
                        return False

            # enfileira próximos apenas se ainda não passamos do limite
            if nivel < k:
                for u in grafo[v]:
                    if u not in visitado and atribuicoes[u] != -1:
                        visitado.add(u)
                        fila.append(u)
        nivel += 1
    return True


"""
    Poda do caso base
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
    Detecta 'unicidade de fornecedor 2' para nós w com f(w)=0 em {v} ∪ N(v).
    - Se nenhum vizinho de w pode ser 2: inviável -> (False).
    - Se exatamente um vizinho x pode ser 2:
        * Se x já é 2: w está coberto, siga adiante -> continue.
        * Se x é indefinido: sugere forçar x=2 -> (True, x).
        * Se x está em {0,1}: contradição -> (False).
    - Caso contrário (>=2 candidatos): nenhuma ação especial -> (True).

    Use contadores para um teste O(1) rápido:
      total_cands = cont_2 + cont_indef = contador_vizinhos[w][2] + contador_vizinhos[w][-1]
      - total_cands == 0  => inviável
      - total_cands == 1  => unicidade; localizar qual é com um loop curto sobre N(w)
    """


def unico_fornecedor_de_dois(contador_vizinhos, grafo, vertice, atribuicoes):
    candidatos_w = [vertice] + grafo[vertice]

    for w in candidatos_w:
        # Só interessa quando w está com f(w)=0
        if atribuicoes[w] != 0:
            continue

        # Passo 1: consultar contadores para decisão rápida
        cont_w = contador_vizinhos[w]
        total_cands = cont_w.get(2, 0) + cont_w.get(-1, 0)

        # Caso A: ninguém pode ser 2 para cobrir w => poda
        if total_cands == 0:
            return (False, None)

        # Caso B: exatamente um candidato pode ser 2 => tentativa de forçar
        if total_cands == 1:
            unico = None

            # Passo 2: identificar o único candidato (evita materializar lista)
            for x in grafo[w]:
                if atribuicoes[x] == 2 or atribuicoes[x] == -1:
                    unico = x
                    break

            # Defesa: se contadores e atribuicoes divergirem
            if unico is None:
                return (False, None)

            # Se já é 2, w está coberto; nada a fazer
            if atribuicoes[unico] == 2:
                continue

            # Se é indefinido, este é um 'forcing move' local: x deve ser 2
            if atribuicoes[unico] == -1:
                return (True, unico)

            # Se chegou aqui, único candidato não é 2 nem indefinido, contradizendo contagem
            return (False, None)

        # Caso C: dois ou mais candidatos possíveis -> não há unicidade; siga
        # continue implícito

    # Nenhum caso de inviabilidade ou unicidade foi detectado
    return True

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
        #print(f"Melhor peso {melhor_peso}")

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
    branch_bound(grafo, atribuicoes, 0, melhor_solucao, melhor_peso, logfile, contador_vizinhos)

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