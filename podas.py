"""
    Funções de podas
    Aumentar a agressividade das podas pode aumentar o custo operacional consideravelmente
"""
from collections import deque

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


def atribuicao_parcial_v2(contador_vizinhos, v, valor):
    if valor == 0:
        # Permite passar se vizinhos ainda não atribuídos existem (-1)
        if contador_vizinhos[v][-1] > 0:
            return True
        return contador_vizinhos[v][2] > 0
    if valor in [1, 2]:
        if contador_vizinhos[v][-1] > 0:
            return True
        return (contador_vizinhos[v][1] + contador_vizinhos[v][2]) > 0
    return False


"""
    Retorna True se v (com f(v) em {1,2}) tem pelo menos um vizinho que pode (realisticamente) ser positivo,
    seja já positivo, seja não atribuído mas sem inviabilidade local se vier a ser 1 ou 2.
"""
def positivo_tem_par_possivel(grafo, atribuicoes, contador_vizinhos, v):
    # já tem vizinho positivo certo?
    if (contador_vizinhos[v][1] + contador_vizinhos[v][2]) > 0:
        return True

    # caso contrário, examinar vizinhos não atribuídos
    for u in grafo[v]:
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
    Checa o próprio v (se positivo) e vizinhos positivos de v; poda se algum ficar sem par possível.
"""
def checar_positivos_isolados_reforcado(grafo, atribuicoes, contador_vizinhos, v):
    # lista de candidatos a checar: v e vizinhos
    candidatos = [v]
    candidatos.extend(grafo[v])

    for x in candidatos:
        val = atribuicoes[x]
        if val in (1, 2):
            # Regra fortalecida: precisa de um par positivo possível
            if not positivo_tem_par_possivel(grafo, atribuicoes, contador_vizinhos, x):
                return False
    return True


"""
    Essa função verifica se existe algum vizinho já atribuído que foi afetado pela escolha atual
    Caso tenha afetado negativamente é feita uma poda
"""
def checar_vizinhos_afetados(contador_vizinhos, grafo, v, atribuicoes):
    # checa inviabilidade em cada u vizinho de v
    for u in grafo[v]:
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
    Dá para incorporar essas três verificações diretamente no caminho quente do branch-and-bound, usando apenas 
    os contadores já mantidos, com custo O(grau(v)) por decisão e sem propagação pesada. A seguir estão funções 
    auxiliares e pontos de integração que implementam: (1) poda imediata para u=0 sem 2 possível, (2) poda imediata 
    para u∈{1,2} sem positivo possível, e (3) detecção de “único fornecedor de 2” para um w com f(w)=0, 
    com opção de restringir o ramo a u=2 ou podar se u≠2.​

    1) Checagens incrementais após fixar v
    Regra A (u=0): se contador_vizinhos[u][-1]==0 e contador_vizinhos[u]==0, 
    então u não tem e não terá vizinho 2, inviável → poda.​

    Regra B (u∈{1,2}): se contador_vizinhos[u][-1]==0 e (contador_vizinhos[u]+contador_vizinhos[u])==0, 
    então u não tem e não terá vizinho positivo, inviável → poda.
"""
def checagens_incrementais_basicas(contador_vizinhos, grafo, atribuicoes, vertice):
    """
    Aplica regras A e B nos vizinhos de v (e opcionalmente em v).
    Retorna False se detectar inviabilidade local imediata; True caso contrário.
    """
    # Checar o próprio v se desejar:
    val_v = atribuicoes[vertice]
    if val_v == 0:
        if contador_vizinhos[vertice][-1] == 0 and contador_vizinhos[vertice][2] == 0:
            return False
    elif val_v in (1, 2):
        if contador_vizinhos[vertice][-1] == 0 and (contador_vizinhos[vertice][1] + contador_vizinhos[vertice][2]) == 0:
            return False

    # Checar os vizinhos afetados
    for u in grafo[vertice]:
        val_u = atribuicoes[u]
        if val_u == -1:
            continue
        if val_u == 0:
            if contador_vizinhos[u][-1] == 0 and contador_vizinhos[u][2] == 0:
                return False
        elif val_u in (1, 2):
            if contador_vizinhos[u][-1] == 0 and (contador_vizinhos[u][1] + contador_vizinhos[u][2]) == 0:
                return False
    return True


"""
    “Único fornecedor de 2” para w com f(w)=0
    Ideia: se algum w com f(w)=0 tem exatamente um vizinho x que ainda pode ser 2 (os demais não podem mais ser 2), 
    então, neste ramo, x precisa ser 2; se você acabou de fixar x com valor diferente de 2, pode podar o ramo; 
    se x ainda está indefinido e você não quer fazer atribuição forçada, ao menos pode recusar valores de x 
    diferentes de 2 (i.e., só continuar quando valor_guarnicao==2).​

    Como testar “pode ser 2”: localmente, um vizinho x pode assumir 2 se não houver proibição imediata; 
    na sua modelagem TRD, colocar 2 em x nunca viola localmente as regras de x, então a viabilidade local depende 
    apenas de não termos bloqueado x por alguma regra adicional; com seus contadores, basta considerar 
    candidatos em {u | atribuicoes[u]==-1 ou atribuicoes[u]==2}.
"""
def unico_fornecedor_de_dois(contador_vizinhos, grafo, atribuicoes, vertice):
    """
    Varre w em {v} ∪ N(v) com f(w)=0 e verifica se existe caso de 'único fornecedor de 2'.
    Retorna:
      - (False, None) se inviável (pois o único fornecedor não é 2 no estado atual);
      - (True, None) se não detectou unicidade;
      - (True, x) se detectou que x é o único fornecedor e x está não atribuído (sugestão para forçar x=2).
    Política: se o único fornecedor x já está atribuído != 2, então retornar (False, None) para podar.
    """
    candidatos_w = [vertice] + grafo[vertice]
    for w in candidatos_w:
        if atribuicoes[w] != 0:
            continue
        # Conte vizinhos que podem ser 2: já 2 ou ainda não atribuídos
        possiveis2 = []
        for x in grafo[w]:
            if atribuicoes[x] == 2:
                possiveis2.append(x)
            elif atribuicoes[x] == -1:
                possiveis2.append(x)
            # atribuicoes[x] == 0 ou 1 não servem para cobrir w

        if len(possiveis2) == 0:
            # Ninguém pode ser 2 para w: inviável
            return (False, None)
        if len(possiveis2) == 1:
            x = possiveis2[0]
            if atribuicoes[x] == 2:
                # já satisfeito, ok
                continue
            elif atribuicoes[x] == -1:
                # x é o único que pode ser 2; sinalize para opcionalmente forçar x=2
                return (True, x)
            else:
                # x foi fixado em {0,1} mas deveria ser 2: inviável
                return (False, None)
    return (True, None)


"""
    Propagação iterativa mais forte

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
def propagar_local(contador_vizinhos, grafo, start_vertices, atribuicoes):
    fila = deque(start_vertices)
    visitado = set()
    while fila:
        v = fila.popleft()
        if v in visitado:
            continue
        visitado.add(v)
        val_v = atribuicoes[v]
        if val_v == -1:
            continue
        # checar inviabilidade de v
        if val_v == 0:
            if contador_vizinhos[v][2] == 0 and contador_vizinhos[v][-1] == 0:
                return False
        elif val_v in (1, 2):
            if (contador_vizinhos[v][1] + contador_vizinhos[v][2]) == 0 and contador_vizinhos[v][-1] == 0:
                return False
        # enfileirar vizinhos que dependem de v
        for u in grafo[v]:
            fila.append(u)
    return True


"""
    Poda de atribuição parcial inválida
"""
def atribuicao_parcial_v1(grafo, atribuicoes):
    n = len(grafo)
    for v in range(n):
        if atribuicoes[v] == -1:
            continue
        if atribuicoes[v] == 0:
            # Verifica apenas vizinhos atribuídos
            vizinhos_atribuidos = [atribuicoes[u] for u in grafo[v] if atribuicoes[u] != -1]

            if vizinhos_atribuidos:
                if 2 not in vizinhos_atribuidos:
                    # Se todos os vizinhos já foram atribuídos e nenhum é 2, falha
                    if all(atribuicoes[u] != -1 for u in grafo[v]):
                        return False
                if not any(x in [1, 2] for x in vizinhos_atribuidos):
                    if all(atribuicoes[u] != -1 for u in grafo[v]):
                        return False

        if atribuicoes[v] in [1, 2]:
            # Verifica apenas vizinhos atribuídos
            # Correção (05.11.25) atribuicoes -> atribuicoes[u]
            vizinhos_atribuidos = [atribuicoes[u] for u in grafo[v] if atribuicoes[u] != -1]

            if vizinhos_atribuidos:
                if not any(x in [1, 2] for x in vizinhos_atribuidos):
                    if all(atribuicoes[u] != -1 for u in grafo[v]):
                        return False
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