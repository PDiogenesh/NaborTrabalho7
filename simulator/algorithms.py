"""
algorithms.py – Algoritmos de busca em redes P2P não estruturadas

Implementa quatro algoritmos (Requisitos III):
  • flooding              – inundação real (redundante, paralela)
  • informed_flooding     – inundação com cache local
  • random_walk           – passeio aleatório puro (burro)
  • informed_random_walk  – passeio aleatório com cache local

Contagem de mensagens (comportamento P2P real):
  • Flooding: cada nó envia para TODOS os seus vizinhos, mesmo que outro nó
    já tenha enviado para o mesmo destino antes. Cada envio = 1 mensagem.
    Quando o recurso é encontrado, os outros ramos já enviados continuam
    sendo contados (pois foram despachados em paralelo).
  • Random walk: cada hop = 1 mensagem. Resposta = 1 mensagem adicional.
"""

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchResult:
    """Resultado completo de uma operação de busca."""
    found: bool
    found_at: Optional[str]       # ID do nó que possui o recurso
    messages: int                  # Total de mensagens trocadas
    nodes_visited: int             # Total de nós envolvidos
    steps: list = field(default_factory=list)  # Log para animação/histórico
    algo: str = ""
    start_node: str = ""
    resource: str = ""
    ttl: int = 0


# ======================================================================
# Helpers
# ======================================================================

def _neighbors_sorted(network, node: str) -> list[str]:
    return sorted(network.adjacency.get(node, set()))


# ======================================================================
# 1. Flooding – Busca por Inundação (comportamento P2P real)
# ======================================================================

def flooding(network, start: str, resource: str, ttl: int) -> SearchResult:
    """
    Comportamento real de flooding P2P:
    - Cada nó envia a query para TODOS os seus vizinhos, sem coordenação global.
    - Um nó só processa a query na primeira vez que a recebe (descarta repetições).
    - Quando o recurso é encontrado, os ramos que já foram despachados em
      paralelo continuam sendo contados (não há como cancelá-los).
    - Isso gera mensagens redundantes, que é o comportamento correto e esperado.
    """
    steps = []
    nodes_visited: set = {start}
    messages = 0
    found = False
    found_at_node = None

    steps.append({"type": "check", "node": start, "resource": resource,
                  "found": resource in network.resources.get(start, [])})
    if resource in network.resources.get(start, []):
        steps.append({"type": "found", "node": start, "resource": resource, "local": True})
        return SearchResult(
            found=True, found_at=start, messages=0, nodes_visited=1, steps=steps,
            algo="flooding", start_node=start, resource=resource, ttl=ttl,
        )

    # Fila: (nó_remetente, nó_destinatário, ttl_restante)
    # Representa mensagens já despachadas mas ainda não processadas.
    queue: deque = deque()

    # Nó inicial despacha para todos os vizinhos
    for neighbor in _neighbors_sorted(network, start):
        messages += 1
        steps.append({"type": "query", "from": start, "to": neighbor,
                      "resource": resource, "ttl": ttl - 1})
        queue.append((start, neighbor, ttl - 1))

    while queue:
        sender, node, cur_ttl = queue.popleft()

        # Nó já processou uma query antes — descarta esta (mas a mensagem já foi contada)
        if node in nodes_visited:
            steps.append({"type": "duplicate", "node": node, "from": sender})
            continue

        nodes_visited.add(node)
        steps.append({"type": "check", "node": node, "resource": resource,
                      "found": resource in network.resources.get(node, [])})

        if resource in network.resources.get(node, []):
            messages += 1  # Mensagem de resposta de volta ao início
            steps.append({"type": "found", "node": node, "resource": resource})
            steps.append({"type": "response", "from": node, "to": start, "resource": resource})
            network.cache[start][resource] = node
            found = True
            found_at_node = node
            # Não para aqui — continua processando a fila para contar mensagens
            # redundantes que já foram despachadas em paralelo
            continue

        if cur_ttl <= 0:
            steps.append({"type": "ttl_expired", "node": node})
            continue

        # Propaga para todos os vizinhos (sem saber quem já recebeu)
        for neighbor in _neighbors_sorted(network, node):
            if neighbor == sender:
                continue  # Não devolve para quem enviou (mas enviaria para todos os outros)
            messages += 1
            steps.append({"type": "query", "from": node, "to": neighbor,
                          "resource": resource, "ttl": cur_ttl - 1})
            queue.append((node, neighbor, cur_ttl - 1))

    if not found:
        steps.append({"type": "not_found", "resource": resource})

    return SearchResult(
        found=found, found_at=found_at_node, messages=messages,
        nodes_visited=len(nodes_visited), steps=steps,
        algo="flooding", start_node=start, resource=resource, ttl=ttl,
    )


# ======================================================================
# 2. Informed Flooding – Inundação com Cache
# ======================================================================

def informed_flooding(network, start: str, resource: str, ttl: int) -> SearchResult:
    """
    Inundação informada: igual ao flooding real, mas cada nó consulta seu
    cache antes de propagar. Se encontrar no cache, responde diretamente
    e não propaga mais, economizando mensagens em buscas repetidas.
    """
    steps = []
    nodes_visited: set = {start}
    messages = 0
    found = False
    found_at_node = None

    # Verifica cache do nó inicial
    if resource in network.cache[start]:
        cached_at = network.cache[start][resource]
        steps.append({"type": "cache_hit", "node": start, "resource": resource, "cached_at": cached_at})
        messages += 1  # Query direta ao nó cacheado
        messages += 1  # Resposta
        steps.append({"type": "query", "from": start, "to": cached_at, "resource": resource,
                      "ttl": ttl, "direct": True})
        steps.append({"type": "found", "node": cached_at, "resource": resource, "from_cache": True})
        steps.append({"type": "response", "from": cached_at, "to": start, "resource": resource})
        return SearchResult(
            found=True, found_at=cached_at, messages=messages, nodes_visited=2, steps=steps,
            algo="informed_flooding", start_node=start, resource=resource, ttl=ttl,
        )

    steps.append({"type": "check", "node": start, "resource": resource,
                  "found": resource in network.resources.get(start, [])})
    if resource in network.resources.get(start, []):
        steps.append({"type": "found", "node": start, "resource": resource, "local": True})
        return SearchResult(
            found=True, found_at=start, messages=0, nodes_visited=1, steps=steps,
            algo="informed_flooding", start_node=start, resource=resource, ttl=ttl,
        )

    # Fila: (nó_remetente, nó_destinatário, ttl_restante)
    queue: deque = deque()

    for neighbor in _neighbors_sorted(network, start):
        messages += 1
        steps.append({"type": "query", "from": start, "to": neighbor,
                      "resource": resource, "ttl": ttl - 1})
        queue.append((start, neighbor, ttl - 1))

    while queue:
        sender, node, cur_ttl = queue.popleft()

        if node in nodes_visited:
            steps.append({"type": "duplicate", "node": node, "from": sender})
            continue

        nodes_visited.add(node)

        # Verifica cache do nó antes de verificar localmente
        if resource in network.cache[node]:
            cached_at = network.cache[node][resource]
            steps.append({"type": "cache_hit", "node": node, "resource": resource,
                           "cached_at": cached_at})
            messages += 1
            steps.append({"type": "response", "from": node, "to": start, "resource": resource,
                           "from_cache": True, "found_at": cached_at})
            network.cache[start][resource] = cached_at
            network.cache[sender][resource] = cached_at
            found = True
            found_at_node = cached_at
            continue

        steps.append({"type": "check", "node": node, "resource": resource,
                      "found": resource in network.resources.get(node, [])})

        if resource in network.resources.get(node, []):
            messages += 1
            steps.append({"type": "found", "node": node, "resource": resource})
            steps.append({"type": "response", "from": node, "to": start, "resource": resource})
            network.cache[start][resource] = node
            network.cache[sender][resource] = node
            found = True
            found_at_node = node
            continue

        if cur_ttl <= 0:
            steps.append({"type": "ttl_expired", "node": node})
            continue

        for neighbor in _neighbors_sorted(network, node):
            if neighbor == sender:
                continue
            messages += 1
            steps.append({"type": "query", "from": node, "to": neighbor,
                          "resource": resource, "ttl": cur_ttl - 1})
            queue.append((node, neighbor, cur_ttl - 1))

    if not found:
        steps.append({"type": "not_found", "resource": resource})

    return SearchResult(
        found=found, found_at=found_at_node, messages=messages,
        nodes_visited=len(nodes_visited), steps=steps,
        algo="informed_flooding", start_node=start, resource=resource, ttl=ttl,
    )


# ======================================================================
# 3. Random Walk – Passeio Aleatório Puro (burro)
# ======================================================================

def random_walk(network, start: str, resource: str, ttl: int) -> SearchResult:
    """
    Passeio aleatório puro: escolhe UM vizinho completamente ao acaso,
    sem nenhuma heurística (pode voltar para o nó anterior, pode revisitar).
    Continua até encontrar o recurso ou o TTL zerar.
    """
    steps = []
    nodes_visited: set = {start}
    messages = 0

    steps.append({"type": "check", "node": start, "resource": resource,
                  "found": resource in network.resources.get(start, [])})
    if resource in network.resources.get(start, []):
        steps.append({"type": "found", "node": start, "resource": resource, "local": True})
        return SearchResult(
            found=True, found_at=start, messages=0, nodes_visited=1, steps=steps,
            algo="random_walk", start_node=start, resource=resource, ttl=ttl,
        )

    current = start
    cur_ttl = ttl

    while cur_ttl > 0:
        neighbors = list(network.adjacency.get(current, set()))
        if not neighbors:
            break

        # Puramente aleatório — sem memória do nó anterior
        next_node = random.choice(neighbors)

        messages += 1
        steps.append({"type": "query", "from": current, "to": next_node,
                      "resource": resource, "ttl": cur_ttl - 1})

        nodes_visited.add(next_node)
        steps.append({"type": "check", "node": next_node, "resource": resource,
                      "found": resource in network.resources.get(next_node, [])})

        if resource in network.resources.get(next_node, []):
            messages += 1
            steps.append({"type": "found", "node": next_node, "resource": resource})
            steps.append({"type": "response", "from": next_node, "to": start, "resource": resource})
            network.cache[start][resource] = next_node
            return SearchResult(
                found=True, found_at=next_node, messages=messages,
                nodes_visited=len(nodes_visited), steps=steps,
                algo="random_walk", start_node=start, resource=resource, ttl=ttl,
            )

        current = next_node
        cur_ttl -= 1

    steps.append({"type": "ttl_expired", "node": current, "ttl": 0})
    steps.append({"type": "not_found", "resource": resource})
    return SearchResult(
        found=False, found_at=None, messages=messages,
        nodes_visited=len(nodes_visited), steps=steps,
        algo="random_walk", start_node=start, resource=resource, ttl=ttl,
    )


# ======================================================================
# 4. Informed Random Walk – Passeio Aleatório com Cache
# ======================================================================

def informed_random_walk(network, start: str, resource: str, ttl: int) -> SearchResult:
    """
    Passeio aleatório informado: igual ao random_walk puro, mas cada nó
    visitado consulta seu cache local antes de continuar o passeio.
    """
    steps = []
    nodes_visited: set = {start}
    messages = 0

    # Verifica cache do nó inicial
    if resource in network.cache[start]:
        cached_at = network.cache[start][resource]
        steps.append({"type": "cache_hit", "node": start, "resource": resource, "cached_at": cached_at})
        messages += 1
        messages += 1
        steps.append({"type": "query", "from": start, "to": cached_at, "resource": resource,
                      "ttl": ttl, "direct": True})
        steps.append({"type": "found", "node": cached_at, "resource": resource, "from_cache": True})
        steps.append({"type": "response", "from": cached_at, "to": start, "resource": resource})
        return SearchResult(
            found=True, found_at=cached_at, messages=messages, nodes_visited=2, steps=steps,
            algo="informed_random_walk", start_node=start, resource=resource, ttl=ttl,
        )

    steps.append({"type": "check", "node": start, "resource": resource,
                  "found": resource in network.resources.get(start, [])})
    if resource in network.resources.get(start, []):
        steps.append({"type": "found", "node": start, "resource": resource, "local": True})
        return SearchResult(
            found=True, found_at=start, messages=0, nodes_visited=1, steps=steps,
            algo="informed_random_walk", start_node=start, resource=resource, ttl=ttl,
        )

    current = start
    cur_ttl = ttl

    while cur_ttl > 0:
        neighbors = list(network.adjacency.get(current, set()))
        if not neighbors:
            break

        # Puramente aleatório — sem memória do nó anterior
        next_node = random.choice(neighbors)

        messages += 1
        steps.append({"type": "query", "from": current, "to": next_node,
                      "resource": resource, "ttl": cur_ttl - 1})

        nodes_visited.add(next_node)

        # Verifica cache do próximo nó
        if resource in network.cache[next_node]:
            cached_at = network.cache[next_node][resource]
            steps.append({"type": "cache_hit", "node": next_node, "resource": resource,
                           "cached_at": cached_at})
            messages += 1
            steps.append({"type": "response", "from": next_node, "to": start, "resource": resource,
                           "from_cache": True, "found_at": cached_at})
            network.cache[start][resource] = cached_at
            network.cache[current][resource] = cached_at
            return SearchResult(
                found=True, found_at=cached_at, messages=messages,
                nodes_visited=len(nodes_visited), steps=steps,
                algo="informed_random_walk", start_node=start, resource=resource, ttl=ttl,
            )

        steps.append({"type": "check", "node": next_node, "resource": resource,
                      "found": resource in network.resources.get(next_node, [])})

        if resource in network.resources.get(next_node, []):
            messages += 1
            steps.append({"type": "found", "node": next_node, "resource": resource})
            steps.append({"type": "response", "from": next_node, "to": start, "resource": resource})
            network.cache[start][resource] = next_node
            network.cache[current][resource] = next_node
            return SearchResult(
                found=True, found_at=next_node, messages=messages,
                nodes_visited=len(nodes_visited), steps=steps,
                algo="informed_random_walk", start_node=start, resource=resource, ttl=ttl,
            )

        current = next_node
        cur_ttl -= 1

    steps.append({"type": "ttl_expired", "node": current, "ttl": 0})
    steps.append({"type": "not_found", "resource": resource})
    return SearchResult(
        found=False, found_at=None, messages=messages,
        nodes_visited=len(nodes_visited), steps=steps,
        algo="informed_random_walk", start_node=start, resource=resource, ttl=ttl,
    )
