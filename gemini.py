import time
import random
import networkx as nx
import matplotlib.pyplot as plt
import sys
from typing import Dict, Set, List, Optional, Tuple
import os  # Necessário para manipulação do caminho do arquivo (os.path.basename, etc.)

# --- CONFIGURAÇÃO DE AMBIENTE E VARIÁVEIS GLOBAIS ---

# Define um limite de recursão maior que o número máximo de vértices esperado (V=1000).
# O Branch and Bound (B&B) é um algoritmo de busca em profundidade (DFS)
# e pode atingir uma profundidade de V (número de vértices).
sys.setrecursionlimit(2000)

# Variáveis Globais para armazenar a Melhor Solução Encontrada (Upper Bound)
# Estas variáveis são modificadas durante a execução recursiva do B&B.
global BEST_WEIGHT
global BEST_STATES
BEST_WEIGHT = float('inf')  # Inicializado com peso infinito
BEST_STATES = None  # Inicializado sem solução
BRANCHING_ORDER = [2, 1, 0]  # Heurística de ramificação: Prioriza atribuições mais promissoras (2, depois 1, depois 0)


# ======================================================================
# FUNÇÃO PARA VISUALIZAÇÃO DE GRAFOS
# ======================================================================

def plot_romana_domination_graph(G: Dict[int, Set[int]], states: List[Optional[int]],
                                 filename: str):
    """
    Gera uma imagem do grafo destacando a solução de Dominação Romana Total (DRT).

    A cor do nó reflete o peso:
    - lightgray (Peso 0)
    - salmon (Peso 1 ou 2)
    O rótulo do nó reflete o peso atribuído:
    - 'V{id}' para Peso 0.
    - 'V{id}={peso}' para Peso 1 ou 2.
    A cor da fonte é preta para todos os rótulos.

    Args:
        G (Dict[int, Set[int]]): O grafo no formato de lista de adjacência (1-indexado).
        states (List[Optional[int]]): Lista de pesos (0, 1, 2) para cada vértice (0-indexado).
        filename (str): Caminho completo para salvar o arquivo de imagem (e.g., .png).
    """

    # 1. Conversão e Inicialização
    nx_graph = nx.Graph()
    for u, neighbors in G.items():
        nx_graph.add_node(u)
        for v in neighbors:
            nx_graph.add_edge(u, v)

    # Mapeamento de cores dos NÓS (Cor do círculo) e inicialização dos dicionários de rótulos
    color_map_weights = {0: 'lightgray', 1: 'salmon', 2: 'salmon'}
    node_color_map = {}
    labels_weight_0 = {}
    labels_weight_1_2 = {}

    # Lista de IDs de nós conforme a ordem interna do networkx (para mapeamento seguro de cores)
    nx_nodes = list(nx_graph.nodes())

    # 2. Iteração e Mapeamento de Cores/Rótulos
    for i, weight in enumerate(states):
        node_id = i + 1  # Converte o índice 0-based para o ID do vértice 1-based

        # Mapeia o ID do nó para a cor correspondente (para garantir a ordenação correta)
        color = color_map_weights.get(weight, 'lightgray')
        node_color_map[node_id] = color

        # Define o rótulo com a formatação solicitada (V{id}={peso})
        if weight in (1, 2):
            labels_weight_1_2[node_id] = f'V{node_id}={weight}'
        else:  # Peso 0
            labels_weight_0[node_id] = f'V{node_id}'

    # 3. Desenho do Grafo
    plt.figure(figsize=(12, 10))
    # Usa Spring Layout para posicionamento visualmente agradável
    pos = nx.spring_layout(nx_graph, seed=42)

    # Obtém a lista de cores na ORDEM correta dos nós do networkx (robustez contra desalinhamento)
    ordered_node_colors = [node_color_map.get(node_id) for node_id in nx_nodes]

    # Desenha os nós (bolinhas) com as cores mapeadas
    nx.draw_networkx_nodes(nx_graph, pos, node_color=ordered_node_colors, node_size=800, alpha=0.9)

    # Desenha as arestas
    nx.draw_networkx_edges(nx_graph, pos, width=1.0, alpha=0.5, edge_color='gray')

    # Desenha Rótulos (Peso 1 ou 2) - Cor da fonte PRETA
    if labels_weight_1_2:
        # Usa font_weight='bold' para dar destaque visual ao texto da solução
        nx.draw_networkx_labels(nx_graph, pos, labels=labels_weight_1_2,
                                font_size=10, font_color='black', font_weight='bold')

    # Desenha Rótulos (Peso 0) - Cor da fonte PRETA
    if labels_weight_0:
        nx.draw_networkx_labels(nx_graph, pos, labels=labels_weight_0,
                                font_size=10, font_color='black')

    plt.title("Dominação Romana Total: Destaque em Vértices Selecionados (Peso 1 ou 2)")
    plt.axis('off')

    # 4. Salvamento da Imagem
    plt.savefig(filename)
    plt.close()
    print(f"Grafo salvo em: {filename}")


# ======================================================================
# FUNÇÕES DE UTILIDADE (I/O)
# ======================================================================

def import_graph_and_order(file_path: str) -> Tuple[Dict[int, Set[int]], int, List[int]]:
    """
    Importa um grafo a partir do formato MTX (Matrix Market) e retorna a lista de adjacência
    e uma ordem de visitação dos vértices por grau decrescente (heurística para B&B).

    Returns:
        Tuple[Dict[int, Set[int]], int, List[int]]: Grafo (G), Número total de vértices (V),
                                                   e Vértices ordenados por grau (decrescente).
    """
    G: Dict[int, Set[int]] = {}
    V = 0

    try:
        with open(file_path, 'r') as f:
            f.readline()  # Pula a linha de comentários inicial

            # Lê o cabeçalho para obter o número total de vértices (V)
            try:
                line = f.readline().split()
                if len(line) < 3: raise ValueError("Cabeçalho inválido.")
                V = max(int(line[0]), int(line[1]))  # Assume V é o maior valor do cabeçalho
            except Exception:
                return G, V, []

            # Inicializa a lista de adjacência (G) para todos os V vértices
            for i in range(1, V + 1): G[i] = set()
            max_id = V

            # Lê as arestas
            for line in f:
                parts = line.split()
                if len(parts) < 2: continue
                try:
                    u, v = int(parts[0]), int(parts[1])
                    max_id = max(max_id, u, v)

                    # Trata o caso de IDs de vértice maiores que o declarado no cabeçalho
                    if u not in G: G[u] = set()
                    if v not in G: G[v] = set()

                    # Adiciona arestas (grafo não-direcionado)
                    G[u].add(v)
                    G[v].add(u)
                except ValueError:
                    continue

            # Ajusta V se o max_id for maior que o V inicial
            if max_id > V:
                for i in range(V + 1, max_id + 1):
                    if i not in G: G[i] = set()
                V = max_id
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado no caminho: {file_path}")
        return {}, 0, []

    # Ordenação dos Vértices (Heurística de Busca)
    # A ordem decrescente de grau ajuda o B&B a tomar decisões mais informadas (com maior impacto)
    # no início da árvore de busca.
    vertex_degrees = [(len(G[u_id]), u_id) for u_id in G]
    vertex_degrees.sort(key=lambda x: x[0], reverse=True)
    ordered_vertices = [u_id for degree, u_id in vertex_degrees]

    return G, V, ordered_vertices


# ======================================================================
# PRÉ-PROCESSAMENTO
# ======================================================================

def check_isolated_vertices(G: Dict[int, Set[int]]) -> bool:
    """
    Verifica se o grafo G contém vértices isolados (grau 0).

    A Dominação Romana Total (DRT) exige que cada nó (v) seja dominado por um vizinho (w)
    com peso w>=1, OU o próprio nó (v) deve ter peso v>=1 E ser dominado por um vizinho (w)
    com peso w=2. Um vértice isolado (grau 0) falha em ambas as condições se seu peso for 0.
    Se o peso for > 0, ele nunca será dominado por um vizinho com peso 2,
    tornando o problema insolúvel (peso infinito) na prática.

    Args:
        G (Dict[int, Set[int]]): O grafo representado como lista de adjacência.

    Returns:
        bool: True se houver vértices isolados, False caso contrário.
    """
    for _, neighbors in G.items():
        if not neighbors:
            return True  # Vértice isolado encontrado (conjunto de vizinhos vazio)

    return False


# ======================================================================
# FUNÇÕES DE HEURÍSTICA E PODA (Core B&B)
# ======================================================================

def calculate_lower_bound(G: Dict[int, Set[int]], estados: List[Optional[int]], upper_bound: int) -> Tuple[bool, float]:
    """
    Calcula o Lower Bound (L) para o nó atual da árvore B&B.

    A poda é baseada no princípio: Se L >= Upper Bound (U), o ramo atual é podado.

    Args:
        G (Dict[int, Set[int]]): O grafo.
        estados (List[Optional[int]]): Estado parcial de atribuição de pesos.
        upper_bound (int): O melhor peso total encontrado até o momento (U).

    Returns:
        Tuple[bool, float]: (should_prune, L). True se deve podar, False caso contrário, e o valor de L.
    """
    W_current = 0
    V_U_indices = []  # Lista de índices (0-based) dos vértices não atribuídos (V_U)
    V = len(estados)

    # 1. Determina o Custo Atual (W_current) e V_U
    for u, val in enumerate(estados):
        if val is not None:
            W_current += val
        else:
            V_U_indices.append(u)

    # 🚨 Condição para o Nó Raiz: Impede Poda Trivial
    # Se W_current é 0, estamos no nó raiz ou muito próximos. O Lower Bound nessa fase
    # é tipicamente fraco e não deve podar a busca prematuramente.
    if W_current == 0:
        return False, 0

    # 🚨 TESTE: Poda Rápida com Look-Ahead
    # Aumentou o custo de processamento e por hora não apresentou melhora
    #if check_infeasibility_lookahead(G, estados):
        #return True, float('inf')

    # Passo 1: Poda Rápida (Verificação de Inviabilidade Imediata)
    # Se o estado parcial for irreparavelmente inviável (ex: nó atribuído=0 sem vizinho=2 em V_A),
    # o custo é infinito e o ramo é podado.
    if check_infeasibility(G, estados):
        return True, float('inf')

    # Passo 2: Cálculo do Custo Futuro (L_future)
    # O L_future representa o custo mínimo que ainda precisa ser pago em V_U.
    L_future = lower_bound_future(G, estados, V_U_indices)

    # Passo 3: Regra da Poda
    L = W_current + L_future

    if L >= upper_bound:
        return True, L  # Poda

    return False, L  # Continua a busca


def lower_bound_future(G: Dict[int, Set[int]], estados: List[Optional[int]], V_U_indices: List[int]) -> int:
    """
    Calcula o custo mínimo futuro (L_future) para cobrir os vértices não atribuídos (V_U).
    Utiliza o Lower Bound mais forte entre as heurísticas relaxadas (Trivial, MIS, C1).
    """

    if not V_U_indices:
        return 0

    # 1. Lower Bound Trivial: Mínimo necessário para cobrir N vértices (pelo menos N/3)
    L_trivial = (len(V_U_indices) + 2) // 3

    # 2. Heurística MIS (Maximal Independent Set)
    # Vértices em um MIS de G[V_U] precisam ser cobertos por si mesmos ou vizinhos em V_A.
    I_indices = []
    V_U_set = set(V_U_indices)

    # Encontrar um Conjunto Independente I em G[V_U] (Simplificado)
    for u_index in V_U_indices:
        u_id = u_index + 1
        # Verifica se o vizinho não atribuído é independente em relação ao MIS já formado
        is_independent = all(v_id - 1 not in I_indices for v_id in G[u_id] if v_id - 1 in V_U_set)
        if is_independent:
            I_indices.append(u_index)

    # Calcular o Custo Relaxado L_mis para o MIS (I)
    L_mis = 0
    for u_index in I_indices:
        u_id = u_index + 1

        # Custo mínimo para cobrir u_id, dado o estado PARCIAL de V_A.
        # u_id precisa ser dominado por v>=1 E, se u_id for 0, por v=2.
        has_Va_2 = any(estados[v - 1] == 2 for v in G[u_id] if estados[v - 1] is not None)
        has_Va_12 = any(estados[v - 1] in (1, 2) for v in G[u_id] if estados[v - 1] is not None)

        # Custos mínimos para u_id ser 0, 1 ou 2, considerando as restrições C1 e C2 em V_A.
        cost_0 = 0 if has_Va_2 else float('inf')
        cost_1 = 1 if has_Va_12 else float('inf')
        cost_2 = 2 if has_Va_12 else float('inf')

        # O custo mínimo para u_id é o menor valor válido
        min_cost_u = min(cost_0, cost_1, cost_2)

        # Se for inviável (infinito), o custo mínimo para o LB deve ser 1 (custo do nó)
        L_mis += min_cost_u if min_cost_u != float('inf') else 1

    # 3. APERTO C1: Penalidade (Lower Bound C1)
    # Cada nó u em V_U que não tem vizinho com peso 2 em V_A precisa, ele próprio,
    # ser atribuído a 1 ou 2 (custo mínimo de 1) ou ter um vizinho em V_U atribuído a 2.
    # O aperto mais simples é contar o número de nós que precisam de um '2' urgente.
    c1_penalty = 0
    for u_index in V_U_indices:
        u_id = u_index + 1
        # Verifica se u_id (em V_U) é dominado por um v=2 em V_A
        has_v2_neighbor_in_Va = any(estados[v - 1] == 2 for v in G[u_id] if estados[v - 1] is not None)

        if not has_v2_neighbor_in_Va:
            # Se não for dominado por v=2, ele ou um vizinho em V_U PRECISA de peso 1 ou 2.
            # O bound mais simples é assumir um custo mínimo de 1.
            c1_penalty += 1

    # 4. Combinação: O Lower Bound mais forte sempre vence
    L_total = max(L_trivial, L_mis, c1_penalty)

    return L_total


def check_infeasibility(G: Dict[int, Set[int]], estados: List[Optional[int]]) -> bool:
    """
    Verifica se a atribuição parcial em V_A já viola as regras C1/C2 de forma irreparável.

    A inviabilidade ocorre se um vértice (em V_A ou V_U) não for dominável, mesmo que todos
    os vértices em V_U sejam atribuídos com o peso máximo (2).

    Args:
        G (Dict[int, Set[int]]): O grafo.
        estados (List[Optional[int]]): Estado parcial ou final de atribuição de pesos.

    Returns:
        bool: True se o estado parcial é inviável.
    """
    V = len(estados)

    # PERCORRE TODOS OS VÉRTICES V
    for u_index in range(V):
        u_id = u_index + 1
        val = estados[u_index]

        # 1. VERIFICAÇÃO DE VÉRTICES JÁ ATRIBUÍDOS (V_A)
        if val is not None:

            # Restrição C1: u com valor 0. Precisa de vizinho com valor 2.
            if val == 0:
                # Checa se C1 é SATISFEITO por V_A
                is_c1_satisfied_by_Va = any(estados[v - 1] == 2 for v in G[u_id] if estados[v - 1] is not None)

                if not is_c1_satisfied_by_Va:
                    # Se C1 falhou em V_A, verifica se há esperança em V_U.
                    has_neighbor_in_Vu = any(estados[v - 1] is None for v in G[u_id])
                    if not has_neighbor_in_Vu:
                        return True  # Inviável: C1 falhou e não há vizinhos em V_U para receber peso 2.

            # Restrição C2: u com valor 1 ou 2. Precisa de vizinho com valor 1 ou 2.
            elif val in (1, 2):
                # Checa se C2 é SATISFEITO por V_A
                is_c2_satisfied_by_Va = any(estados[v - 1] in (1, 2) for v in G[u_id] if estados[v - 1] is not None)

                if not is_c2_satisfied_by_Va:
                    # Se C2 falhou em V_A, verifica se há esperança em V_U.
                    has_neighbor_in_Vu = any(estados[v - 1] is None for v in G[u_id])
                    if not has_neighbor_in_Vu:
                        return True  # Inviável: C2 falhou e não há vizinhos em V_U para receber peso 1 ou 2.

        # 2. VERIFICAÇÃO DE VÉRTICES NÃO ATRIBUÍDOS (V_U)
        if val is None:
            # Se u está em V_U, checamos se seus vizinhos em V_A já o condenaram.
            all_neighbors_in_Va = all(estados[v_id - 1] is not None for v_id in G[u_id])

            if all_neighbors_in_Va:
                # Se u só tem vizinhos em V_A, ele deve ser dominado (C2) por V_A.
                has_v12_neighbor_in_Va = any(estados[v_id - 1] in (1, 2) for v_id in G[u_id])

                if not has_v12_neighbor_in_Va:
                    # u_id (em V_U) não é dominado por V_A (C2), e não há esperança em V_U.
                    return True

    return False

"""
    Custo operacional adicional sem identificação de melhorias para os testes realizados
"""
def check_infeasibility_lookahead(G: Dict[int, Set[int]], estados: List[Optional[int]]) -> bool:
    """
    Verifica a inviabilidade do estado parcial (estados) com uma propagação leve (look-ahead k=1).

    Além das checagens normais de inviabilidade imediata, esta função verifica se
    a atribuição atual em V_A CONDENA algum vizinho em V_U a uma situação insolúvel.

    Args:
        G (Dict[int, Set[int]]): O grafo.
        estados (List[Optional[int]]): Estado parcial de atribuição de pesos.

    Returns:
        bool: True se o estado for inviável e deve ser podado.
    """
    V = len(estados)
    V_U_indices = {i for i, val in enumerate(estados) if val is None}

    # ----------------------------------------------------------------------
    # 1. VERIFICAÇÃO DE INVIABILIDADE IMEDIATA (Lógica Original)
    #    Checa se V_A já violou C1 ou C2 e não há esperança em V_U.
    # ----------------------------------------------------------------------
    for u_index in range(V):
        u_id = u_index + 1
        val = estados[u_index]
        u_neighbors_in_Vu = any(estados[v - 1] is None for v in G.get(u_id, set()))

        # Checagem de C1/C2 em V_A (como na função original)
        if val is not None:

            # C1 (val=0): Precisa de vizinho com peso 2.
            if val == 0:
                is_c1_satisfied_by_Va = any(estados[v - 1] == 2
                                            for v in G.get(u_id, set())
                                            if estados[v - 1] is not None)
                if not is_c1_satisfied_by_Va and not u_neighbors_in_Vu:
                    return True  # Inviável: C1 falhou e não há vizinhos em V_U para corrigir.

            # C2 (val=1 ou 2): Precisa de vizinho com peso 1 ou 2.
            elif val in (1, 2):
                is_c2_satisfied_by_Va = any(estados[v - 1] in (1, 2)
                                            for v in G.get(u_id, set())
                                            if estados[v - 1] is not None)
                if not is_c2_satisfied_by_Va and not u_neighbors_in_Vu:
                    return True  # Inviável: C2 falhou e não há vizinhos em V_U para corrigir.

        # Checagem de Dominação em V_U (u_index pertence a V_U)
        if val is None:
            all_neighbors_in_Va = all(estados[v_id - 1] is not None for v_id in G.get(u_id, set()))
            if all_neighbors_in_Va:
                has_v12_neighbor_in_Va = any(estados[v_id - 1] in (1, 2) for v_id in G.get(u_id, set()))
                if not has_v12_neighbor_in_Va:
                    return True  # Inviável: Nó em V_U não é dominado e só tem vizinhos em V_A.

    # ----------------------------------------------------------------------
    # 2. PROPAGAÇÃO LEVE (LOOK-AHEAD k=1)
    #    Checa se algum nó 'w' em V_U será inevitavelmente inviável em breve.
    # ----------------------------------------------------------------------
    for w_index in V_U_indices:
        w_id = w_index + 1

        # Checagem C1: Assume que o nó 'w' será atribuído a 0 (pior caso para C1)
        # Se w=0, ele precisa de um vizinho com peso 2.

        # 1. Checa a satisfação de C1 para w=0, considerando V_A.
        is_c1_satisfied_by_Va_for_w = any(estados[v - 1] == 2
                                          for v in G.get(w_id, set())
                                          if estados[v - 1] is not None)

        if not is_c1_satisfied_by_Va_for_w:
            # Se V_A não satisfaz C1 (v=2), a satisfação depende de V_U.

            # 2. Simula o pior cenário: Se todos os vizinhos de w em V_U forem atribuídos a 0 ou 1.
            # O nó 'w' só pode satisfazer C1 se um vizinho v_vu em V_U for atribuído a 2.
            # Se todos os vizinhos de w em V_U já foram atribuídos a 0 ou 1, C1 falhará.

            # Condição de Falha: w só tem vizinhos em V_A ou vizinhos V_U já testados
            # (na verdade, checamos se existe pelo menos um vizinho em V_U que ainda pode ser 2)
            has_Vu_neighbor_for_v2 = any(v_id - 1 in V_U_indices for v_id in G.get(w_id, set()))

            if not has_Vu_neighbor_for_v2:
                # Condição mais forte (simplesmente)
                # Se w não tem vizinhos em V_U, C1 será inviável se w for 0.
                # Esta checagem é coberta pela seção 1, mas é reforçada aqui.
                pass

    return False  # Nenhuma inviabilidade detectada (poda não necessária)

# ======================================================================
# FUNÇÕES GULOSA (Upper Bound)
# ======================================================================

def greedy_romana_domination(G: Dict[int, Set[int]], ordered_vertices: List[int]) -> Tuple[List[int], int]:
    """
    Heurística gulosa construtiva para encontrar uma Dominação Romana Total (DRT) válida.

    A heurística foca em satisfazer C2 (dominação por peso >= 1) e depois C1 (ajuste por peso = 2).
    A ordem de visitação dos vértices influencia a qualidade do resultado.

    Returns:
        Tuple[List[int], int]: O estado (estados_guloso) e o peso total (current_weight).
    """
    V = len(G)
    estados_guloso = [0] * V
    current_weight = 0

    # Passo 1: Satisfação C2 (Dominação Simples)
    # Percorre os vértices em ordem (decrescente de grau ou aleatória).
    for u_id in ordered_vertices:
        u_index = u_id - 1

        # Verifica se o nó u_id já é dominado por um vizinho com peso 1 ou 2.
        is_dominated_by_neighbor = any(estados_guloso[v_id - 1] in (1, 2) for v_id in G[u_id])

        # Se u_id não for dominado e seu peso atual for < 1, força v(u)=1.
        if not is_dominated_by_neighbor and estados_guloso[u_index] < 1:
            estados_guloso[u_index] = 1
            current_weight += 1

    # Passo 2: Satisfação C1 (Ajuste para Dominação Romana)
    # Agora, garante que todos os nós com peso 0 sejam dominados por um vizinho com peso 2.
    for u_id in range(1, V + 1):
        u_index = u_id - 1

        if estados_guloso[u_index] == 0:
            # Verifica se C1 está satisfeito (vizinho com peso 2)
            has_v2_neighbor = any(estados_guloso[v_id - 1] == 2 for v_id in G[u_id])

            if not has_v2_neighbor:
                # C1 falhou. É preciso aumentar o peso de um vizinho para 2.
                best_neighbor_id = None
                max_degree_change = -1  # Heurística: Prioriza o vizinho de maior grau

                for v_id in G[u_id]:
                    v_index = v_id - 1

                    # Custo para subir para 2 (de 0 ou 1)
                    cost_to_2 = 2 - estados_guloso[v_index]

                    if cost_to_2 > 0:
                        current_degree = len(G[v_id])
                        if current_degree > max_degree_change:
                            max_degree_change = current_degree
                            best_neighbor_id = v_id

                # Realiza o ajuste (Atribui o vizinho de maior grau a 2)
                if best_neighbor_id is not None:
                    best_neighbor_index = best_neighbor_id - 1
                    cost_increase = 2 - estados_guloso[best_neighbor_index]

                    estados_guloso[best_neighbor_index] = 2
                    current_weight += cost_increase

    return estados_guloso, current_weight


def find_best_greedy_u(G: Dict[int, Set[int]], ordered_vertices: List[int], attempts: int = 10) -> Tuple[
    int, List[int]]:
    """
    Executa a heurística gulosa múltiplas vezes com ordens de vértices diferentes
    para encontrar um Upper Bound (U) inicial de alta qualidade para o B&B.

    Args:
        G (Dict[int, Set[int]]): O grafo.
        ordered_vertices (List[int]): Vértices ordenados por grau (primeira tentativa).
        attempts (int): Número de execuções da heurística.

    Returns:
        Tuple[int, List[int]]: O melhor peso Upper Bound encontrado e o estado correspondente.
    """
    best_u = float('inf')
    best_states = None

    orders = [list(ordered_vertices)]  # 1. Primeira ordem (por grau)

    # 2. Gera (attempts - 1) ordens aleatórias
    for _ in range(attempts - 1):
        random_order = list(ordered_vertices)
        random.shuffle(random_order)
        orders.append(random_order)

    # Executa a heurística gulosa para cada ordem
    for current_order in orders:
        states, weight = greedy_romana_domination(G, current_order)

        if weight < best_u:
            best_u = weight
            best_states = states

    # Condição de Falha (Grafo muito grande ou inviável, retorna um bound trivial)
    if best_u == float('inf'):
        V = len(G)
        return 2 * V, [2] * V  # Bound seguro, mas alto

    return int(best_u), best_states


# ======================================================================
# FUNÇÕES DE RAMIFICAÇÃO (Branch and Bound)
# ======================================================================

def bb_recursive(G: Dict[int, Set[int]],
                 V: int,
                 ordered_vertices: List[int],
                 estados: List[Optional[int]],
                 current_weight: int,
                 list_index: int):
    """
    Função recursiva principal (DFS) do Branch and Bound.

    Esta função explora o espaço de busca, podando ramos inviáveis ou não-promissores.

    Args:
        G, V: Grafo e número de vértices.
        ordered_vertices: Ordem de visitação dos vértices.
        estados: O estado de atribuição de pesos (solução parcial).
        current_weight: Peso acumulado da solução parcial (W_current).
        list_index: Índice do vértice atual a ser ramificado (u).
    """
    global BEST_WEIGHT
    global BEST_STATES

    # Log do peso
    print(f"Atual: {current_weight} Melhor: {BEST_WEIGHT} ")

    # 1. CRITÉRIO DE PARADA: Solução Completa
    # Se todos os vértices foram atribuídos (o índice passou do último vértice),
    # o estado 'estados' é uma solução final.
    if list_index >= V:
        if current_weight < BEST_WEIGHT:
            # Checagem Final: Garante que a solução completa é realmente viável.
            is_valid_final = not check_infeasibility(G, estados)

            if is_valid_final:
                BEST_WEIGHT = current_weight
                BEST_STATES = list(estados)

        return

    # 2. RAMIFICAÇÃO (Para o vértice atual 'u')
    u_id = ordered_vertices[list_index]  # ID do vértice (1-based)
    u_index = u_id - 1  # Índice do vértice (0-based)

    # A ordem de ramificação (2, 1, 0) é uma heurística para encontrar bons bounds
    # mais rapidamente, priorizando pesos mais altos.
    for value in BRANCHING_ORDER:

        new_estados = list(estados)
        new_estados[u_index] = value
        new_weight = current_weight + value

        # ⛔ PODA TRIVIAL E RÁPIDA: Custo Atual vs. Upper Bound
        # Se o custo parcial já excede o melhor encontrado, não há necessidade de prosseguir.
        if new_weight >= BEST_WEIGHT:
            continue

        # 3. ETAPA DE PODA (Lower Bound Check)
        # Calcula o Lower Bound (L) = W_current + L_future.
        should_prune, _ = calculate_lower_bound(G, new_estados, BEST_WEIGHT)

        if should_prune:
            continue  # PODA EXECUTADA (L >= BEST_WEIGHT ou Inviabilidade)

        # 4. CHAMADA RECURSIVA: Procede para o próximo vértice
        bb_recursive(G, V, ordered_vertices, new_estados, new_weight, list_index + 1)


def branch_and_bound_romana(G: Dict[int, Set[int]], ordered_vertices: List[int]) -> Tuple[
    Optional[List[int]], Optional[int]]:
    """
    Função wrapper para inicializar o Branch and Bound (B&B).
    Define o Upper Bound inicial e inicia a busca recursiva.

    Returns:
        Tuple[Optional[List[int]], Optional[int]]: O melhor estado e o melhor peso encontrados.
    """
    V = len(ordered_vertices)
    global BEST_WEIGHT
    global BEST_STATES

    # 1. Inicializa o Upper Bound (U) com a solução Gulosa Otimizada
    # Uma boa solução inicial (U) é crucial para a eficácia das podas.
    best_u, best_u_states = find_best_greedy_u(G, ordered_vertices, attempts=10)

    # Inicializa as variáveis globais do B&B
    BEST_WEIGHT = best_u
    BEST_STATES = best_u_states

    print("---------------------------------------------------------")
    print(f"UPPER BOUND (U) GULOSO INICIAL: {BEST_WEIGHT}")
    print("---------------------------------------------------------")

    # Inicializa o estado B&B (todos os vértices não atribuídos = None)
    estados_iniciais = [None] * V

    # Inicia a busca DFS (recursão)
    bb_recursive(G, V, ordered_vertices, estados_iniciais, 0, 0)

    return BEST_STATES, BEST_WEIGHT


def run_and_measure_romana_domination(file_path: str):
    """Função principal que gerencia o fluxo de execução, mede o tempo e apresenta os resultados."""
    print(f"Iniciando processamento para: {file_path} ---")

    # 1. Carregamento e Ordenação do Grafo
    G, V, ordered_vertices = import_graph_and_order(file_path)

    # 2. PRÉ-PROCESSAMENTO: VERIFICAÇÃO DE VÉRTICES ISOLADOS
    if check_isolated_vertices(G):
        # Levanta exceção, pois a DRT não é possível (Peso infinito)
        raise ValueError(
            "O grafo é inválido para Dominação Romana Total: Contém vértices isolados (grau 0). "
            "A DRT não pode ser formada."
        )

    if V == 0:
        print("Erro: Grafo não carregado ou vazio.")
        return

    # 3. Execução e Medição de Tempo
    start_time = time.perf_counter()
    best_estados, best_weight = branch_and_bound_romana(G, ordered_vertices)
    end_time = time.perf_counter()
    execution_time = end_time - start_time

    # 4. Apresentação de Resultados
    if best_estados is None:
        print("\n❌ Solução não encontrada ou grafo inviável (o B&B pode ter sido parado cedo).")
        print(f"Tempo de Execução: {execution_time:.2f} segundos")
        return

    print("RESULTADOS DO PROBLEMA DE DOMINAÇÃO ROMANA TOTAL")
    print("---------------------------------------------------------")
    print(f"Peso Total Mínimo Encontrado: {best_weight}")
    print(f"Tempo de Execução: {execution_time:.2f} segundos")
    print("Atribuições de Pesos por Vértice (1 ou 2) (v: peso)")

    # Filtra e formata apenas os vértices com peso 1 ou 2
    vertices_selecionados = []
    for i, peso in enumerate(BEST_STATES):
        vertice_id = i + 1
        if peso in (1, 2):
            vertices_selecionados.append(f"v{vertice_id}: {peso}")

    # Impressão formatada em blocos de 10
    if vertices_selecionados:
        chunk_size = 10
        for j in range(0, len(vertices_selecionados), chunk_size):
            linha = " | ".join(vertices_selecionados[j:j + chunk_size])
            print(linha)
    else:
        print("Nenhum vértice com peso 1 ou 2 encontrado. (Solução W=0 ou erro)")

    print("---------------------------------------------------------")

    # 5. Visualização do Grafo
    # Cria o caminho absoluto para o arquivo de imagem
    output_dir = os.path.join(os.path.dirname(file_path), r"imagens")
    os.makedirs(output_dir, exist_ok=True)
    graph_name = os.path.basename(file_path).replace(".mtx", "_romana_plot.png")
    output_filename = os.path.join(output_dir, graph_name)

    plot_romana_domination_graph(G, BEST_STATES, output_filename)


# ======================================================================
# EXECUÇÃO DO SCRIPT
# ======================================================================

# Arquivos em ordem pelo tamanho do arquivo
# Arquivos com V=1000 impõe recursão de V e deixa a máquina bem lenta em razão da profundidade
# Considere mínimo a primeira função.
#   Se tiver ? é porque não terminou de rodar
#   Se for observado que o número baixou muito eu colocarei o valor

# Log em bb_recursive após as variáveis globais

arquivo = r"matrizes\johnson8-2-4.mtx" # V=28 A=210 - Pesos: mínimo 6 - guloso 9 - gemini 6 (guloso 6)
#arquivo = r"matrizes\hamming6-4.mtx" # V=64 A=704 - Pesos: mínimo ? (parei em 8) - guloso 24 - gemini 16 (guloso 16)
#arquivo = r"matrizes\MANN-a9.mtx" # V=45 A=918 - Pesos: mínimo 4 - guloso 8 - gemini 4 (guloso 4)
#arquivo = r"matrizes\johnson8-4-4.mtx" # V=70 A=1855 - Pesos: mínimo 4 - guloso 13 - gemini 6 (guloso 8)
#arquivo = r"matrizes\c-fat200-2.mtx" # V=200 A=3235 - Pesos: mínimo ? (parei em 113) - guloso 27 - gemini 28 (guloso 28)
#arquivo = r"matrizes\johnson16-2-4.mtx" # V=120 A=5460 - Pesos: mínimo ? (parei em 7) - guloso 9 - gemini 6 (guloso 6)
#arquivo = r"matrizes\C1000-9.mtx" # V=1000 A=450.079 - Pesos: mínimo ? - guloso 9 - gemini 6 (guloso 8)

run_and_measure_romana_domination(arquivo)