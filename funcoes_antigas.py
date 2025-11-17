import collections
import time
import random
import networkx as nx
import matplotlib.pyplot as plt
import sys
from typing import Dict, Set, List, Optional, Tuple

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