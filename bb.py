import math
import random
import time
import networkx as nx
import matplotlib.pyplot as plt
import os
import pandas as pd

from typing import Dict, Set, List, Optional, Tuple
#from turtle import pd

# Variáveis Globais para armazenar a Melhor Solução Encontrada (Upper Bound)
# Estas variáveis são modificadas durante a execução recursiva do B&B.
global BEST_WEIGHT
BEST_WEIGHT = float('inf')  # Inicializado com peso infinito
global BEST_STATES
BEST_STATES = None  # Inicializado sem solução
global RESULTADOS
RESULTADOS: List[Tuple[str, bool, bool, str, int, float]] = []
# List[Tuple[técnica, nome_grafo, peso, tempo]]
global BRANCHING_ORDER
BRANCHING_ORDER = [2, 1, 0]  # Heurística de ramificação: Prioriza atribuições mais promissoras (2, depois 1, depois 0)


# ======================================================================
# FUNÇÃO PARA VISUALIZAÇÃO DE GRAFOS
# ======================================================================

def plotar_grafico(G: Dict[int, Set[int]], states: List[Optional[int]], arquivo: str, tecnica: str, is_lower_bound: bool, is_upper_bound: bool):
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

    lower = "S_LB"
    upper = "S_UB"

    if is_lower_bound:
        lower = "LB"

    if is_upper_bound:
        upper = "UB"

    if extensao.lower() == '.mtx':
        graph_name = os.path.basename(arquivo).replace(".mtx", f"_{tecnica}_{lower}_{upper}.png")
    elif extensao.lower() == '.txt':
        graph_name = os.path.basename(arquivo).replace(".txt", f"_{tecnica}_{lower}_{upper}.png")

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
              F"Branch and Bound ({lower} - {upper}) - Pesos 1 e 2 em vermelho")
    plt.axis('off')

    # 4. Salvamento da Imagem
    plt.savefig(filename)
    plt.close()
    #print(f"Grafo salvo em: {filename}")

# ======================================================================
# FUNÇÕES DE UTILIDADE (I/O)
# ======================================================================

def importar_base0(file_path: str) -> Tuple[Dict[int, Set[int]], int, List[int]]:
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

def importar_base1(file_path: str) -> Tuple[Dict[int, Set[int]], int, List[int]]:
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

def recuperar_lista_arquivos(nome_pasta: str):
    """
    Abre a pasta especificada e gera uma lista com os nomes de todos
    os arquivos e diretórios contidos nela.

    Args:
        nome_pasta (str): O nome da pasta a ser aberta.
                          Assume que a pasta está no mesmo diretório
                          que o script em execução.

    Returns:
        list: Uma lista de strings contendo os nomes dos arquivos e diretórios.
    """
    try:
        # Usa os.listdir() para obter todos os nomes de arquivos e pastas no caminho
        lista_de_itens = os.listdir(nome_pasta)

        # Filtra para incluir apenas os arquivos.
        # Você pode remover esta parte se quiser incluir subpastas também.
        apenas_arquivos = []
        for item in lista_de_itens:
            caminho_completo = os.path.join(nome_pasta, item)
            if os.path.isfile(caminho_completo):
                apenas_arquivos.append(item)

        return apenas_arquivos

    except FileNotFoundError:
        print(f"Erro: A pasta '{nome_pasta}' não foi encontrada.")
        return []
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return []

def exportar_excel(nome_arquivo: str = 'resultados.xlsx', sheet_name: str = 'Resultados B&B'):
    """
        Exporta o conteúdo da lista global RESULTADOS_GRAFOS_BRANCH_AND_BOUND
        para um arquivo Excel.

        Args:
            nome_arquivo (str): Nome do arquivo Excel a ser criado.
            sheet_name (str): Nome da planilha dentro do arquivo Excel.
        """
    global RESULTADOS

    if not RESULTADOS:
        print("⚠️ A lista de resultados está vazia. Nenhuma exportação para Excel realizada.")
        return

    try:
        # 1. Cria o DataFrame do Pandas a partir da lista de tuplas global
        df = pd.DataFrame(RESULTADOS, columns=['Algoritmo', 'Com lower bound?', 'Com upper bound?', 'Grafo', 'Peso', 'Segundos', 'Vértices com peso'])

        # 2. Exporta o DataFrame para o Excel
        # index=False: Evita que o índice numérico padrão do Pandas seja escrito no Excel.
        df.to_excel(nome_arquivo, index=False, sheet_name=sheet_name, engine='openpyxl')
        #df.to_excel(nome_arquivo, index=False, sheet_name=sheet_name, engine='xlsxwriter')

        print("\n" + "=" * 50)
        print(f"🎉 Exportação concluída com sucesso!")
        print(f"Arquivo: '{nome_arquivo}' | Total de {len(df)} registros.")
        print("=" * 50)

    except ImportError:
        print("❌ ERRO: A biblioteca 'openpyxl' (ou 'xlsxwriter') não está instalada.")
        print("Instale-a usando: pip install openpyxl")
    except Exception as e:
        print(f"❌ Ocorreu um erro durante a exportação: {e}")

def adicionar_resultado(tecnica: str, is_lower_bound: bool, is_upper_bound: bool, nome_grafo: str, peso_encontrado: int, tempo: float, vertices_selecionados: []):
    """
    Adiciona o nome do grafo e o peso calculado à lista global.
    """
    global RESULTADOS

    # Adiciona o novo resultado como uma tupla (nome, peso)
    RESULTADOS.append((tecnica, is_lower_bound, is_upper_bound, nome_grafo, peso_encontrado, tempo, vertices_selecionados))
    #print(f"Resultado adicionado: Grafo '{nome_grafo}', Peso: {peso_encontrado}")

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

    return vertices_selecionados

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
# Lower bound
# ======================================================================

def lower_bound(G: Dict[int, Set[int]], estados: List[Optional[int]], current_weight: int) -> int:
    """
    Calcula o Lower Bound (LB) para a Dominação Romana Total, respeitando
    a restrição de que nenhum vértice com peso >= 1 pode ser isolado (deve ter vizinho >= 1).
    """
    lower_bound = current_weight
    V = len(estados)
    V_U = {i + 1 for i, val in enumerate(estados) if val is None}
    total_min_demand = 0.0

    for v_id in range(1, V + 1):
        v_index = v_id - 1
        v_val = estados[v_index]
        N_v = G.get(v_id, set())

        # 1. Vértices vizinhos em V_U (potenciais doadores de peso)
        N_v_U = N_v.intersection(V_U)
        count_N_v_U = len(N_v_U)

        # 2. Vértices vizinhos em V_A com peso >= 1 (Guarnições existentes)
        N_v_VA_guarrison = {w for w in N_v if estados[w - 1] is not None and estados[w - 1] >= 1}

        # Se um nó em V_A precisa de correção, mas não tem vizinhos em V_U, o ramo é inviável
        # (Assumimos que 'verificar_inviabilidade_local' já trata isso).
        if count_N_v_U == 0 and v_val is not None and not bool(N_v_VA_guarrison) and len(N_v) > 0:
            continue

        # --- CÁLCULO DA DEMANDA MÍNIMA DE V_U (As Três Regras) ---

        # Regra 1: Demanda de Vértices V_A com peso 0 (Exigem w=2 - C1)
        if v_val == 0:
            if not any(estados[w - 1] == 2 for w in N_v_VA_guarrison):
                # Não é reforçado por um vizinho V_A=2, exige w=2 de V_U
                if count_N_v_U > 0:
                    total_min_demand += 2.0 / count_N_v_U

        # Regra 2: Demanda de Vértices V_A com peso >= 1 (Exigem Conexão w>=1 - NOVO C1)
        elif v_val in (1, 2):
            if not N_v_VA_guarrison:
                # Guarnição está isolada em V_A, exige w=1 de V_U
                if count_N_v_U > 0:
                    total_min_demand += 1.0 / count_N_v_U

        # Regra 3: Demanda de Vértices V_U (Exigem Dominação C2 w>=1)
        elif v_val is None:
            # v ∈ V_U: verifica se v é dominado por um vizinho V_A >= 1 (Dominação C2)
            is_C2_dominated_by_VA = bool(N_v_VA_guarrison)

            if not is_C2_dominated_by_VA:
                # Não é dominado por V_A, exige w=1 para dominação própria (C2)
                # O custo mínimo de dominação é 1 (peso 1)
                total_options = count_N_v_U + 1  # v + N(v) ∩ V_U (inclui o próprio v)
                total_min_demand += 1.0 / total_options

    # O Lower Bound final é o peso atual mais a demanda total, arredondado para cima.
    lower_bound += int(math.ceil(total_min_demand))

    return lower_bound

def lower_bound_future(G: Dict[int, Set[int]], estados: List[Optional[int]], V_U_indices: List[int]) -> int:
    """
    Calcula o custo mínimo futuro (L_future) para cobrir os vértices não atribuídos (V_U).
    Utiliza o Lower Bound mais forte entre as heurísticas relaxadas (Trivial, MIS, C1).
    """

    if not V_U_indices:
        return 0

    # Apenas para depuração ou correção rápida:
    V_U_indices = [idx for idx in V_U_indices if idx is not None]

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

# ======================================================================
# Upper Bound
# ======================================================================

def upper_bound_guloso(G: Dict[int, Set[int]], ordered_vertices: List[int]) -> Tuple[List[int], int]:
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

    # --- NOVO PASSO 3: SATISFAÇÃO DA RESTRIÇÃO DE CONECTIVIDADE (VÉRTICES >= 1 NÃO ISOLADOS) ---

    # Re-verifica todos os vértices para garantir que os vértices com peso >= 1 estejam conectados.
    # V é o número total de vértices
    V = len(G)
    for v_id in range(1, V + 1):
        v_index = v_id - 1

        # 1. Verifica se o vértice v TEM peso >= 1
        if estados_guloso[v_index] >= 1:

            # 2. Verifica se ele TEM um vizinho w com peso >= 1
            has_v1_neighbor = False
            for w_id in G[v_id]:  # Itera sobre os vizinhos
                if estados_guloso[w_id - 1] >= 1:
                    has_v1_neighbor = True
                    break

            # 3. Se C1 para peso positivo falhar (não tem vizinho >= 1)
            if not has_v1_neighbor:

                # RESTRIÇÃO C1 VIOLADA! Devemos atribuir peso 1 ao vizinho mais estratégico.

                # Escolhe o vizinho que será atribuído v=1 para satisfazer a regra.
                # Usamos o vizinho de maior grau entre os com peso 0 para maximizar o impacto.
                best_neighbor_id = None
                max_degree = -1

                for w_id in G[v_id]:
                    w_index = w_id - 1
                    # Só podemos modificar vértices que ainda estão com peso 0
                    if estados_guloso[w_index] == 0:
                        current_degree = len(G.get(w_id, set()))
                        if current_degree > max_degree:
                            max_degree = current_degree
                            best_neighbor_id = w_id

                # Aplica a correção: Atribui 1 ao vizinho escolhido
                if best_neighbor_id is not None:
                    best_neighbor_index = best_neighbor_id - 1
                    estados_guloso[best_neighbor_index] = 1  # Atribui peso 1
                    current_weight += 1

    # A função greedy_romana_domination deve retornar o current_weight e estados_guloso
    #return current_weight, estados_guloso

    return estados_guloso, current_weight

def melhor_peso_guloso(G: Dict[int, Set[int]], ordered_vertices: List[int], attempts: int = 10) -> Tuple[
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
        states, weight = upper_bound_guloso(G, current_order)

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
                 list_index: int,
                 is_lower_bound: bool):
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

                # Log de mudança de valor
                #print(f"Peso atualizado: {BEST_WEIGHT}")

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

        # ⛔ PODA TRIVIAL E RÁPIDA: Custo Atual vs. Upper Bound
        # Se o custo parcial já excede o melhor encontrado, não há necessidade de prosseguir.
        if new_weight >= BEST_WEIGHT:
            continue

        if is_lower_bound:
            if lower_bound(G, new_estados, 0) + new_weight >= BEST_WEIGHT:
                continue
            #if new_weight + lower_bound_future(G, new_estados, new_estados) >= BEST_WEIGHT:
            #    continue

        bb_recursive(G, V, ordered_vertices, new_estados, new_weight, list_index + 1, is_lower_bound)

def branch_and_bound(G: Dict[int, Set[int]], ordered_vertices: List[int], is_lower_bound: bool, is_upper_bound: bool) -> Tuple[
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

    if is_upper_bound:
        # 1. Inicializa o Upper Bound (U) com a solução Gulosa Otimizada
        # Uma boa solução inicial (U) é crucial para a eficácia das podas.
        best_u, best_u_states = melhor_peso_guloso(G, ordered_vertices, attempts=10)

        # Inicializa as variáveis globais do B&B
        BEST_WEIGHT = best_u
        BEST_STATES = best_u_states

        print("---------------------------------------------------------")
        print(f"UPPER BOUND (U) GULOSO INICIAL: {BEST_WEIGHT}")
        print("---------------------------------------------------------")

    # Inicializa o estado B&B (todos os vértices não atribuídos = None)
    estados_iniciais = [None] * V

    # Inicia a busca DFS (recursão)
    bb_recursive(G, V, ordered_vertices, estados_iniciais, 0, 0, is_lower_bound)

    return BEST_STATES, BEST_WEIGHT

def dominacao(tecnica: str, arquivo: str, pasta: str, is_lower_bound: bool, is_upper_bound: bool):
    """Função principal que gerencia o fluxo de execução, mede o tempo e apresenta os resultados."""
    print("---------------------------------------------------------")
    print(f"Iniciando processamento ({tecnica}) para: {arquivo}")
    print("---------------------------------------------------------")

    # 1. Carregamento e Ordenação do Grafo
    _, extensao = os.path.splitext(arquivo)
    local_arquivo = pasta + arquivo

    # Diferença para indicar se o índice do grafo começa em 0 ou 1
    #G, V, vertices_ordenados = importar_base0(local_arquivo)
    G, V, vertices_ordenados = importar_base1(local_arquivo)

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

    # REINICIALIZAÇÃO
    global BEST_WEIGHT
    global BEST_STATES
    BEST_WEIGHT = float('inf')  # Reset para o B&B começar do zero
    BEST_STATES = None

    melhores_estados, melhor_peso = branch_and_bound(G, vertices_ordenados, is_lower_bound, is_upper_bound)

    """if tecnica.lower() == "puro":
        melhores_estados, melhor_peso = branch_and_bound(G, vertices_ordenados, is_lower_bound, is_upper_bound)
    elif tecnica.lower() == "guloso":
        melhores_estados, melhor_peso = branch_and_bound_h_gulosa(G, vertices_ordenados)"""

    # 3. Execução e Medição de Tempo
    end_time = time.perf_counter()
    tempo_total = end_time - start_time

    # 4. Impressão do resultado
    vertices_selecionados = impressao_resultado(melhores_estados, melhor_peso, tempo_total)

    # 5. Adiciona o resultado para uma lista de exportação
    adicionar_resultado(tecnica, is_lower_bound, is_upper_bound, arquivo, melhor_peso, round(tempo_total, 2), vertices_selecionados)

    # 6. Plotagem do Grafo
    plotar_grafico(G, BEST_STATES, arquivo, tecnica, is_lower_bound, is_upper_bound)

# ======================================================================
# EXECUÇÃO DO SCRIPT
# ======================================================================

#pasta: str
pasta = "grafos\\"

# Recuperação da lista de arquivos
arquivos_encontrados = recuperar_lista_arquivos(pasta)
if arquivos_encontrados:
    print(f"✅ Arquivos encontrados em {pasta}:")
    #for arquivo in arquivos_encontrados:
    #    print(f"{arquivo}")
else:
    print("❌ Não foram encontrados arquivos, ou a pasta não existe.")

# Operação de dominação romana
for grafo in arquivos_encontrados:
    dominacao('B&B', grafo, pasta, False, False)
    dominacao('B&B', grafo, pasta, False, True)
    dominacao('B&B', grafo, pasta, True, False)
    dominacao('B&B', grafo, pasta, True, True)

exportar_excel()