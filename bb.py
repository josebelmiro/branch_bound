import time
import random
from collections import deque
from operator import concat

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

def plotar_grafico(G: Dict[int, Set[int]], states: List[Optional[int]], arquivo: str):
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

    # Cria o caminho absoluto para o arquivo de imagem
    output_dir = os.path.join(os.path.dirname(arquivo), r"imagens")
    os.makedirs(output_dir, exist_ok=True)

    _, extensao = os.path.splitext(arquivo)

    if extensao.lower() == '.mtx':
        graph_name = os.path.basename(arquivo).replace(".mtx", ".png")
    elif extensao.lower() == '.txt':
        graph_name = os.path.basename(arquivo).replace(".txt", ".png")

    filename = os.path.join(output_dir, graph_name)

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

    plt.title(F"Dominação Romana Total: {arquivo}\n"
              F"Em vermelho (Peso 1 ou 2)")
    plt.axis('off')

    # 4. Salvamento da Imagem
    plt.savefig(filename)
    plt.close()
    #print(f"Grafo salvo em: {filename}")

# ======================================================================
# FUNÇÕES DE UTILIDADE (I/O)
# ======================================================================

def importar_grafo_mtx(file_path: str) -> Tuple[Dict[int, Set[int]], int, List[int]]:
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


from typing import Dict, Set, List, Optional, Tuple


def importar_grafo_txt(file_path: str) -> Tuple[Dict[int, Set[int]], int, List[int]]:
    """
    Importa um grafo a partir de um arquivo de lista de arestas (0-based)
    com cabeçalho simples (V V E), como o formato 'grafo-70-0-0.7.txt'.

    Realiza a conversão dos IDs de vértice de 0-based (arquivo) para 1-based (código B&B).

    Returns:
        Tuple[Dict[int, Set[int]], int, List[int]]: Grafo (G, 1-based),
                                                   Número total de vértices (V),
                                                   e Vértices ordenados por grau (decrescente).
    """
    G: Dict[int, Set[int]] = {}
    V = 0
    max_id_lido = 0  # O maior ID lido no arquivo (0-based)

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

            # 1. Processamento do Cabeçalho (Pula comentários e linhas vazias, e lê V E)
            data_start_line = 0

            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith(('%', '#')):
                    continue

                parts = line.split()
                try:
                    # O cabeçalho deve ser a primeira linha não comentada com V V E.
                    if len(parts) >= 3 and parts[2].isdigit():
                        # Vértices são V e arestas são E
                        V_lido = int(parts[0])
                        # Atualiza V, o loop de dados deve começar na linha seguinte
                        V = V_lido
                        data_start_line = i + 1
                    break
                except ValueError:
                    # Se falhar, assume que esta é a primeira linha de dados.
                    break

                    # 2. Leitura e Processamento das Arestas (A partir de data_start_line)
            for line in lines[data_start_line:]:
                parts = line.split()
                if len(parts) < 2: continue
                try:
                    u_0based, v_0based = int(parts[0]), int(parts[1])

                    # 💥 CONVERSÃO PARA 1-BASED
                    u = u_0based + 1
                    v = v_0based + 1

                    # Rastreia o ID máximo (agora 1-based)
                    max_id_lido = max(max_id_lido, u, v)

                    # Adiciona arestas
                    if u not in G: G[u] = set()
                    if v not in G: G[v] = set()

                    # Grafo não-direcionado
                    G[u].add(v)
                    G[v].add(u)
                except ValueError:
                    continue

            # 3. Ajuste Final e Inicialização de Vértices
            # Usa o maior valor lido para V, caso o cabeçalho esteja errado ou ausente.
            V = max(V, max_id_lido)

            # Garante que todos os vértices (1 a V) existam no dicionário G, mesmo se forem isolados.
            for i in range(1, V + 1):
                if i not in G: G[i] = set()

    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado no caminho: {file_path}")
        return {}, 0, []

    # 4. Ordenação dos Vértices (Heurística de Busca por Grau Decrescente)
    vertex_degrees = [(len(G.get(u_id, set())), u_id) for u_id in range(1, V + 1)]
    vertex_degrees.sort(key=lambda x: x[0], reverse=True)
    ordered_vertices = [u_id for degree, u_id in vertex_degrees]

    return G, V, ordered_vertices

def impressao_resultado(melhores_estados, melhor_peso, tempo_total):
    """
        Apresentação de Resultados
    """
    if melhores_estados is None:
        print("\n❌ Solução não encontrada ou grafo inviável (o B&B pode ter sido parado cedo).")
        print(f"Tempo de Execução: {tempo_total:.2f} segundos")
        return

    print("DOMINAÇÃO ROMANA TOTAL")
    print(f"Menor peso: {melhor_peso}")
    print("Vértices com peso 1 ou 2 (v: peso)")

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
    print(f"Tempo de execução: {tempo_total:.2f} segundos")
    print("---------------------------------------------------------")

# ======================================================================
# PRÉ-PROCESSAMENTO
# ======================================================================

def vertices_isolados(G: Dict[int, Set[int]]) -> bool:
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

def atribuicao_valida(G: Dict[int, Set[int]], estados: List[Optional[int]]) -> bool:
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

# ======================================================================
# FUNÇÕES DE PODA (Branch and Bound)
# ======================================================================

from typing import Dict, Set, List, Optional, Tuple


def calculate_lower_bound(G: Dict[int, Set[int]], estados: List[Optional[int]], current_weight: int) -> int:
    lower_bound = current_weight

    for u_id in G.keys():
        u_index = u_id - 1

        # Ignora vértices já atribuídos
        if estados[u_index] is not None:
            continue

        # -------------------------------------------------------------
        # CALCULA A CONTRIBUIÇÃO MÍNIMA NECESSÁRIA (0, 1, ou 2)
        # -------------------------------------------------------------
        min_contribution = 0
        is_dominated_by_Va_ge1 = False

        # Itera sobre os vizinhos do nó u (em V_U)
        for v_id in G.get(u_id, set()):
            v_index = v_id - 1
            v_val = estados[v_index]

            # VIZINHO EM V_A
            if v_val is not None:

                # A. Checa dominação trivial (Restrição C2)
                if v_val in (1, 2):
                    is_dominated_by_Va_ge1 = True

                # B. Checa a necessidade de w=2 (Restrição C1)
                if v_val == 1:
                    # Vizinho v com w=1 precisa de um vizinho com w=2 (para dominação romana)
                    # Checa se o requisito w=2 já está satisfeito por V_A
                    has_w2_neighbor_in_Va = any(estados[w_id - 1] == 2
                                                for w_id in G[v_id]
                                                if estados[w_id - 1] is not None and w_id != u_id)

                    if not has_w2_neighbor_in_Va:
                        # Se v (w=1) não é dominado por um w=2 em V_A, ele precisa de alguém em V_U.
                        # Se u é o único em V_U que pode fornecê-lo:

                        vizinhos_Vu_v = {w_id for w_id in G[v_id] if estados[w_id - 1] is None}

                        # Se u é o ÚNICO em V_U que pode satisfazer v (w=1):
                        if len(vizinhos_Vu_v) == 1 and u_id in vizinhos_Vu_v:
                            # A contribuição mínima de u tem que ser 2 para satisfazer v
                            min_contribution = max(min_contribution, 2)

            # VIZINHO EM V_U (LB Fraco: Ignorado para manter a complexidade)
            # Para LB mais forte, você faria emparelhamento ou outra análise em V_U

        # -------------------------------------------------------------
        # FINALIZAÇÃO DA CONTRIBUIÇÃO PARA O LB
        # -------------------------------------------------------------

        if not is_dominated_by_Va_ge1 and min_contribution < 1:
            # Se u não é dominado por V_A (C2), e a Restrição C1 não o forçou a 2, ele precisa de pelo menos 1.
            min_contribution = max(min_contribution, 1)

        lower_bound += min_contribution

    return lower_bound


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
    #print(f"Melhor: {BEST_WEIGHT}, Atual: {current_weight} ")

    # 1. CRITÉRIO DE PARADA: Solução Completa
    # Se todos os vértices foram atribuídos (o índice passou do último vértice),
    # o estado 'estados' é uma solução final.
    if list_index >= V:
        if current_weight < BEST_WEIGHT:
            # Checagem Final: Garante que a solução completa é realmente viável.
            is_valid_final = not atribuicao_valida(G, estados)

            if is_valid_final:
                BEST_WEIGHT = current_weight
                BEST_STATES = list(estados)

        return

    # Passo 1: Poda Rápida (Verificação de Inviabilidade Imediata)
    # Se o estado parcial for irreparavelmente inviável (ex: nó atribuído=0 sem vizinho=2 em V_A),
    # o custo é infinito e o ramo é podado.
    if atribuicao_valida(G, estados):
        return True, float('inf')

    # 2. RAMIFICAÇÃO (Para o vértice atual 'u')
    u_id = ordered_vertices[list_index]  # ID do vértice (1-based)
    u_index = u_id - 1  # Índice do vértice (0-based)

    # A ordem de ramificação (2, 1, 0) é uma heurística para encontrar bons bounds
    # mais rapidamente, priorizando pesos mais altos.
    for value in BRANCHING_ORDER:

        new_estados = list(estados)
        new_estados[u_index] = value
        new_weight = current_weight + value

        # 1. Se u_id foi atribuído 0, checa se ele está condenado
        if value == 0:
            # Se u_id=0, ele precisa de um vizinho w=2.
            # Se TODOS os vizinhos N(u) já foram atribuídos (V_A), e nenhum é w=2, o ramo é inviável.
            vizinhos_Va = {v for v in G.get(u_id) if new_estados[v - 1] is not None}
            if not G.get(u_id) or len(vizinhos_Va) == len(G.get(u_id)):  # Todos em V_A
                if not any(new_estados[v - 1] == 2 for v in vizinhos_Va):
                    continue  # Poda: u=0 está condenado.

        # 2. Checa se u_id é um fornecedor OBRIGATÓRIO (w=2)
        # Se u_id é vizinho de algum w' que obriga u_id a ser w=2, e 'value' não é 2, poda.
        for w_id in G.get(u_id, set()):
            w_index = w_id - 1
            w_val = new_estados[w_index]

            # Só checamos se o vizinho w é um nó de peso 0 já atribuído
            if w_val == 0:
                # Re-calculamos a esperança de w
                vizinhos_Va_w = {v for v in G.get(w_id) if new_estados[v - 1] is not None}
                vizinhos_Vu_w = {v for v in G.get(w_id) if new_estados[v - 1] is None}

                tem_w2_em_Va = any(new_estados[v - 1] == 2 for v in vizinhos_Va_w)

                # Se w precisa de w=2 e u_id é o ÚNICO que sobrou em V_U
                if not tem_w2_em_Va and len(vizinhos_Vu_w) == 1 and u_id in vizinhos_Vu_w:
                    # Se u_id é o fornecedor obrigatório, mas value não é 2, PODA!
                    if value != 2:
                        continue  # Poda: Obrigação de w=2 violada.

        # ⛔ PODA TRIVIAL E RÁPIDA: Custo Atual vs. Upper Bound
        # Se o custo parcial já excede o melhor encontrado, não há necessidade de prosseguir.
        if new_weight >= BEST_WEIGHT:
            continue

        # Poda de lower bound
        if new_weight + 1 >= BEST_WEIGHT:
            continue



        # 4. CHAMADA RECURSIVA: Procede para o próximo vértice
        bb_recursive(G, V, ordered_vertices, new_estados, new_weight, list_index + 1)

def branch_and_bound(G: Dict[int, Set[int]], ordered_vertices: List[int]) -> Tuple[
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

    # Inicializa o estado B&B (todos os vértices não atribuídos = None)
    estados_iniciais = [None] * V

    # Inicia a busca DFS (recursão)
    bb_recursive(G, V, ordered_vertices, estados_iniciais, 0, 0)

    return BEST_STATES, BEST_WEIGHT

def dominacao(arquivo: str):
    """Função principal que gerencia o fluxo de execução, mede o tempo e apresenta os resultados."""
    print("---------------------------------------------------------")
    print(f"Iniciando processamento para: {arquivo}")
    print("---------------------------------------------------------")


    # 1. Carregamento e Ordenação do Grafo
    pasta_mtx = "matrizes\\"
    pasta_txt = "grafos_aleatorios\\"

    _, extensao = os.path.splitext(arquivo)

    if extensao.lower() == '.mtx':
        local_arquivo = pasta_mtx + arquivo
        G, V, vertices_ordenados = importar_grafo_mtx(local_arquivo)
    elif extensao.lower() == '.txt':
        local_arquivo = pasta_txt + arquivo
        G, V, vertices_ordenados = importar_grafo_txt(local_arquivo)

    # 2. PRÉ-PROCESSAMENTO: VERIFICAÇÃO DE VÉRTICES ISOLADOS
    if vertices_isolados(G):
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
    melhores_estados, melhor_peso = branch_and_bound(G, vertices_ordenados)
    end_time = time.perf_counter()
    tempo_total = end_time - start_time

    # 4. Impressão do resultado
    impressao_resultado(melhores_estados, melhor_peso, tempo_total)

    # 5. Plotagem do Grafo
    plotar_grafico(G, BEST_STATES, arquivo)

# ======================================================================
# EXECUÇÃO DO SCRIPT
# ======================================================================

arquivo = "johnson8-2-4.mtx" # V=28 A=210 - Pesos: bb 6 - bb_h_gulosa 6 (guloso 6)
#arquivo = "hamming6-4.mtx" # V=64 A=704 - Pesos: bb ? (parei em 8) - bb_h_gulosa 16 (guloso 16)
#arquivo = "MANN-a9.mtx" # V=45 A=918 - Pesos: bb 4 - bb_h_gulosa 4 (guloso 4)
#arquivo = "johnson8-4-4.mtx" # V=70 A=1855 - Pesos: bb 4 - bb_h_gulosa 6 (guloso 8)
#arquivo = "c-fat200-2.mtx" # V=200 A=3235 - Pesos: bb ? (parei em 113) - bb_h_gulosa 28 (guloso 28)
#arquivo = "johnson16-2-4.mtx" # V=120 A=5460 - Pesos: bb ? (parei em 7) - bb_h_gulosa 6 (guloso 6)
#arquivo = "C1000-9.mtx" # V=1000 A=450.079 - Pesos: bb ? - bb_h_gulosa 6 (guloso 8)

#arquivo = "grafo-70-0-0.7.txt"

dominacao(arquivo)