from collections import deque

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