"""
algorithms.py – Algoritmos de busca em redes P2P não estruturadas

Implementa quatro algoritmos (Requisitos III):
  • flooding              – inundação pura
  • informed_flooding     – inundação com cache local
  • random_walk           – passeio aleatório puro
  • informed_random_walk  – passeio aleatório com cache local

Contagem de mensagens:
  • Cada envio de query de um nó a um vizinho = 1 mensagem
  • A resposta (quando o recurso é encontrado) = 1 mensagem adicional
  • Total = mensagens de query + mensagem de resposta (se encontrado)
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
    steps: list = field(default_factory=list)  # Log para animação
    algo: str = ""
    start_node: str = ""
    resource: str = ""
    ttl: int = 0


# ======================================================================
# Helpers
# ======================================================================

def _neighbors_sorted(network, node: str) -> list[str]:
    """Retorna vizinhos ordenados (determinismo em testes)."""
    return sorted(network.adjacency.get(node, set()))


# ======================================================================
# 1. Flooding – Busca por Inundação
# ======================================================================

def flooding(network, start: str, resource: str, ttl: int) -> SearchResult:
    """
    Envia a query para TODOS os vizinhos de cada nó visitado.
    Propaga em largura (BFS) até TTL=0 ou até encontrar o recurso.

    Complexidade de mensagens: O(n) no pior caso (todos os nós).
    """
    steps = []
    nodes_visited: set = {start}
    messages = 0

    # Verifica o nó inicial
    steps.append({"type": "check", "node": start, "resource": resource,
                  "found": resource in network.resources.get(start, [])})
    if resource in network.resources.get(start, []):
        steps.append({"type": "found", "node": start, "resource": resource, "local": True})
        return SearchResult(
            found=True, found_at=start, messages=0, nodes_visited=1, steps=steps,
            algo="flooding", start_node=start, resource=resource, ttl=ttl,
        )

    # BFS: (nó_atual, ttl_restante)
    queue: deque = deque([(start, ttl)])

    while queue:
        node, cur_ttl = queue.popleft()
        if cur_ttl <= 0:
            continue

        for neighbor in _neighbors_sorted(network, node):
            if neighbor in nodes_visited:
                continue  # Nó já recebeu a query – descarta duplicata

            nodes_visited.add(neighbor)
            messages += 1  # Mensagem de query enviada

            steps.append({
                "type": "query",
                "from": node,
                "to": neighbor,
                "resource": resource,
                "ttl": cur_ttl - 1,
            })
            steps.append({
                "type": "check",
                "node": neighbor,
                "resource": resource,
                "found": resource in network.resources.get(neighbor, []),
            })

            if resource in network.resources.get(neighbor, []):
                messages += 1  # Mensagem de resposta
                steps.append({"type": "found", "node": neighbor, "resource": resource})
                steps.append({"type": "response", "from": neighbor, "to": start, "resource": resource})
                # Atualiza cache do nó que iniciou a busca
                network.cache[start][resource] = neighbor
                return SearchResult(
                    found=True, found_at=neighbor, messages=messages,
                    nodes_visited=len(nodes_visited), steps=steps,
                    algo="flooding", start_node=start, resource=resource, ttl=ttl,
                )

            if cur_ttl - 1 > 0:
                queue.append((neighbor, cur_ttl - 1))
            else:
                steps.append({"type": "ttl_expired", "node": neighbor})

    steps.append({"type": "not_found", "resource": resource})
    return SearchResult(
        found=False, found_at=None, messages=messages,
        nodes_visited=len(nodes_visited), steps=steps,
        algo="flooding", start_node=start, resource=resource, ttl=ttl,
    )


# ======================================================================
# 2. Informed Flooding – Inundação com Cache
# ======================================================================

def informed_flooding(network, start: str, resource: str, ttl: int) -> SearchResult:
    """
    Inundação informada: cada nó consulta seu cache antes de propagar.
    Se o cache indica onde o recurso está, a resposta é enviada diretamente
    sem propagar a query mais adiante (economizando mensagens em buscas repetidas).
    """
    steps = []
    nodes_visited: set = {start}
    messages = 0

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

    # Verifica o nó inicial (possui o recurso?)
    steps.append({"type": "check", "node": start, "resource": resource,
                  "found": resource in network.resources.get(start, [])})
    if resource in network.resources.get(start, []):
        steps.append({"type": "found", "node": start, "resource": resource, "local": True})
        return SearchResult(
            found=True, found_at=start, messages=0, nodes_visited=1, steps=steps,
            algo="informed_flooding", start_node=start, resource=resource, ttl=ttl,
        )

    # BFS: (nó_atual, ttl_restante)
    queue: deque = deque([(start, ttl)])

    while queue:
        node, cur_ttl = queue.popleft()
        if cur_ttl <= 0:
            continue

        for neighbor in _neighbors_sorted(network, node):
            if neighbor in nodes_visited:
                continue

            nodes_visited.add(neighbor)
            messages += 1  # Mensagem de query

            steps.append({
                "type": "query",
                "from": node,
                "to": neighbor,
                "resource": resource,
                "ttl": cur_ttl - 1,
            })

            # Verifica cache do vizinho (busca informada)
            if resource in network.cache[neighbor]:
                cached_at = network.cache[neighbor][resource]
                steps.append({"type": "cache_hit", "node": neighbor, "resource": resource,
                               "cached_at": cached_at})
                messages += 1  # Resposta com info do cache
                steps.append({"type": "response", "from": neighbor, "to": start, "resource": resource,
                               "from_cache": True, "found_at": cached_at})
                # Propaga o cache para o nó inicial
                network.cache[start][resource] = cached_at
                network.cache[node][resource] = cached_at
                return SearchResult(
                    found=True, found_at=cached_at, messages=messages,
                    nodes_visited=len(nodes_visited), steps=steps,
                    algo="informed_flooding", start_node=start, resource=resource, ttl=ttl,
                )

            steps.append({
                "type": "check",
                "node": neighbor,
                "resource": resource,
                "found": resource in network.resources.get(neighbor, []),
            })

            if resource in network.resources.get(neighbor, []):
                messages += 1  # Resposta
                steps.append({"type": "found", "node": neighbor, "resource": resource})
                steps.append({"type": "response", "from": neighbor, "to": start, "resource": resource})
                # Atualiza caches ao longo do caminho
                network.cache[start][resource] = neighbor
                network.cache[node][resource] = neighbor
                return SearchResult(
                    found=True, found_at=neighbor, messages=messages,
                    nodes_visited=len(nodes_visited), steps=steps,
                    algo="informed_flooding", start_node=start, resource=resource, ttl=ttl,
                )

            if cur_ttl - 1 > 0:
                queue.append((neighbor, cur_ttl - 1))
            else:
                steps.append({"type": "ttl_expired", "node": neighbor})

    steps.append({"type": "not_found", "resource": resource})
    return SearchResult(
        found=False, found_at=None, messages=messages,
        nodes_visited=len(nodes_visited), steps=steps,
        algo="informed_flooding", start_node=start, resource=resource, ttl=ttl,
    )


# ======================================================================
# 3. Random Walk – Passeio Aleatório
# ======================================================================

def random_walk(network, start: str, resource: str, ttl: int) -> SearchResult:
    """
    Encaminha a query para UM vizinho escolhido aleatoriamente.
    Continua até encontrar o recurso ou o TTL chegar a zero.

    Complexidade de mensagens: O(TTL) – muito menor que flooding.
    Nota: pode revisitar nós (comportamento esperado em passeio aleatório).
    """
    steps = []
    nodes_visited: set = {start}
    messages = 0

    # Verifica o nó inicial
    steps.append({"type": "check", "node": start, "resource": resource,
                  "found": resource in network.resources.get(start, [])})
    if resource in network.resources.get(start, []):
        steps.append({"type": "found", "node": start, "resource": resource, "local": True})
        return SearchResult(
            found=True, found_at=start, messages=0, nodes_visited=1, steps=steps,
            algo="random_walk", start_node=start, resource=resource, ttl=ttl,
        )

    current = start
    prev = None
    cur_ttl = ttl

    while cur_ttl > 0:
        neighbors = list(network.adjacency.get(current, set()))
        if not neighbors:
            break

        # Prefere não voltar para o nó anterior (heurística básica)
        options = [n for n in neighbors if n != prev]
        if not options:
            options = neighbors  # Sem alternativa, aceita voltar

        next_node = random.choice(options)

        messages += 1  # Query enviada
        steps.append({
            "type": "query",
            "from": current,
            "to": next_node,
            "resource": resource,
            "ttl": cur_ttl - 1,
        })

        nodes_visited.add(next_node)
        steps.append({
            "type": "check",
            "node": next_node,
            "resource": resource,
            "found": resource in network.resources.get(next_node, []),
        })

        if resource in network.resources.get(next_node, []):
            messages += 1  # Resposta
            steps.append({"type": "found", "node": next_node, "resource": resource})
            steps.append({"type": "response", "from": next_node, "to": start, "resource": resource})
            network.cache[start][resource] = next_node
            return SearchResult(
                found=True, found_at=next_node, messages=messages,
                nodes_visited=len(nodes_visited), steps=steps,
                algo="random_walk", start_node=start, resource=resource, ttl=ttl,
            )

        prev = current
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
    Passeio aleatório informado: cada nó visitado consulta seu cache local.
    Se o cache indica onde o recurso está, responde diretamente sem continuar
    o passeio.
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

    # Verifica o nó inicial
    steps.append({"type": "check", "node": start, "resource": resource,
                  "found": resource in network.resources.get(start, [])})
    if resource in network.resources.get(start, []):
        steps.append({"type": "found", "node": start, "resource": resource, "local": True})
        return SearchResult(
            found=True, found_at=start, messages=0, nodes_visited=1, steps=steps,
            algo="informed_random_walk", start_node=start, resource=resource, ttl=ttl,
        )

    current = start
    prev = None
    cur_ttl = ttl

    while cur_ttl > 0:
        neighbors = list(network.adjacency.get(current, set()))
        if not neighbors:
            break

        options = [n for n in neighbors if n != prev]
        if not options:
            options = neighbors

        next_node = random.choice(options)

        messages += 1
        steps.append({
            "type": "query",
            "from": current,
            "to": next_node,
            "resource": resource,
            "ttl": cur_ttl - 1,
        })

        nodes_visited.add(next_node)

        # Verifica cache do próximo nó (busca informada)
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

        steps.append({
            "type": "check",
            "node": next_node,
            "resource": resource,
            "found": resource in network.resources.get(next_node, []),
        })

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

        prev = current
        current = next_node
        cur_ttl -= 1

    steps.append({"type": "ttl_expired", "node": current, "ttl": 0})
    steps.append({"type": "not_found", "resource": resource})
    return SearchResult(
        found=False, found_at=None, messages=messages,
        nodes_visited=len(nodes_visited), steps=steps,
        algo="informed_random_walk", start_node=start, resource=resource, ttl=ttl,
    )
