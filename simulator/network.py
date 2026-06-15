"""
network.py – Classe P2PNetwork
Carrega, valida e representa uma rede P2P não estruturada a partir de um arquivo JSON.
"""

import json
from collections import defaultdict, deque


class ValidationError(Exception):
    """Erro de validação da estrutura da rede P2P."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


class P2PNetwork:
    """
    Representa uma rede P2P não estruturada.

    Atributos:
        num_nodes (int): número declarado de nós
        min_neighbors (int): grau mínimo por nó
        max_neighbors (int): grau máximo por nó
        nodes (set): conjunto de todos os IDs de nós
        resources (dict): {node_id: [resource_ids]}
        adjacency (dict): {node_id: set(neighbor_ids)}
        cache (dict): {node_id: {resource_id: node_id_com_o_recurso}}
    """

    def __init__(self):
        self.num_nodes = 0
        self.min_neighbors = 0
        self.max_neighbors = float("inf")
        self.nodes: set = set()
        self.resources: dict = {}
        self.adjacency: dict = defaultdict(set)
        self.cache: dict = {}
        self._raw_config: dict = {}

    # ------------------------------------------------------------------
    # Carregamento
    # ------------------------------------------------------------------

    @classmethod
    def load_from_file(cls, filepath: str) -> "P2PNetwork":
        """Carrega a rede a partir de um arquivo JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls._from_dict(data)

    @classmethod
    def load_from_string(cls, json_string: str) -> "P2PNetwork":
        """Carrega a rede a partir de uma string JSON."""
        data = json.loads(json_string)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> "P2PNetwork":
        net = cls()
        net._raw_config = data

        net.num_nodes = int(data.get("num_nodes", 0))
        net.min_neighbors = int(data.get("min_neighbors", 0))
        net.max_neighbors = int(data.get("max_neighbors", 10**9))

        # Recursos
        for node, res_list in data.get("resources", {}).items():
            net.nodes.add(node)
            net.resources[node] = list(res_list)

        # Arestas
        for edge in data.get("edges", []):
            n1, n2 = str(edge[0]), str(edge[1])
            net.nodes.add(n1)
            net.nodes.add(n2)
            net.adjacency[n1].add(n2)
            net.adjacency[n2].add(n1)

        # Garante que todos os nós existam no adjacency (mesmo sem arestas)
        for node in list(net.nodes):
            if node not in net.adjacency:
                net.adjacency[node] = set()

        # Inicializa cache vazio para cada nó
        for node in net.nodes:
            net.cache[node] = {}

        return net

    # ------------------------------------------------------------------
    # Validação (Requisitos II)
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """
        Valida a estrutura da rede. Lança ValidationError com todos os problemas
        encontrados (não para no primeiro erro).

        Regras verificadas:
          1. num_nodes bate com a contagem real de nós
          2. Sem arestas de loop (nó → ele mesmo)
          3. Nenhum nó sem recursos
          4. Grau de cada nó está entre min_neighbors e max_neighbors
          5. Rede não está particionada (conexa)
        """
        errors: list[str] = []

        # Regra 1 – contagem de nós
        real_count = len(self.nodes)
        if real_count != self.num_nodes:
            errors.append(
                f"[Regra 1] num_nodes={self.num_nodes}, mas a rede tem {real_count} nó(s) real(is)."
            )

        # Regra 2 – sem loops
        for node in sorted(self.nodes):
            if node in self.adjacency.get(node, set()):
                errors.append(f"[Regra 2] Aresta de loop detectada no nó '{node}'.")

        # Regra 3 – sem nós sem recursos
        for node in sorted(self.nodes):
            if node not in self.resources or len(self.resources[node]) == 0:
                errors.append(f"[Regra 3] Nó '{node}' não possui nenhum recurso.")

        # Regra 4 – grau mín/máx
        for node in sorted(self.nodes):
            degree = len(self.adjacency.get(node, set()))
            if degree < self.min_neighbors:
                errors.append(
                    f"[Regra 4] Nó '{node}' tem {degree} vizinho(s) (mínimo: {self.min_neighbors})."
                )
            if degree > self.max_neighbors:
                errors.append(
                    f"[Regra 4] Nó '{node}' tem {degree} vizinho(s) (máximo: {self.max_neighbors})."
                )

        # Regra 5 – conectividade (sem partição)
        if self.nodes:
            start = next(iter(self.nodes))
            visited: set = set()
            queue: deque = deque([start])
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                for neighbor in self.adjacency.get(node, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)

            unreachable = sorted(self.nodes - visited)
            if unreachable:
                errors.append(
                    f"[Regra 5] Rede particionada. Nó(s) inacessível(is): {unreachable}."
                )

        if errors:
            raise ValidationError(errors)

    # ------------------------------------------------------------------
    # Busca (despacha para o algoritmo escolhido)
    # ------------------------------------------------------------------

    def search(self, node_id: str, resource_id: str, ttl: int, algo: str):
        """Executa uma operação de busca e retorna um SearchResult."""
        from simulator.algorithms import (
            flooding,
            informed_flooding,
            random_walk,
            informed_random_walk,
        )

        algo_map = {
            "flooding": flooding,
            "informed_flooding": informed_flooding,
            "random_walk": random_walk,
            "informed_random_walk": informed_random_walk,
        }

        if algo not in algo_map:
            raise ValueError(
                f"Algoritmo '{algo}' desconhecido. Opções: {list(algo_map.keys())}"
            )
        if node_id not in self.nodes:
            raise ValueError(f"Nó '{node_id}' não existe na rede.")
        if ttl < 0:
            raise ValueError("TTL deve ser >= 0.")

        return algo_map[algo](self, node_id, resource_id, ttl)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def reset_cache(self) -> None:
        """Reseta todos os caches locais dos nós."""
        for node in self.nodes:
            self.cache[node] = {}

    def all_resources(self) -> list[str]:
        """Retorna lista ordenada de todos os recursos na rede."""
        res = set()
        for lst in self.resources.values():
            res.update(lst)
        return sorted(res)

    def to_dict(self) -> dict:
        """Serializa a rede para JSON (usado pela API)."""
        return {
            "num_nodes": self.num_nodes,
            "min_neighbors": self.min_neighbors,
            "max_neighbors": self.max_neighbors,
            "nodes": [
                {
                    "id": node,
                    "resources": self.resources.get(node, []),
                    "neighbors": sorted(self.adjacency.get(node, set())),
                    "degree": len(self.adjacency.get(node, set())),
                }
                for node in sorted(self.nodes)
            ],
            "edges": [
                [n1, n2]
                for n1 in sorted(self.nodes)
                for n2 in sorted(self.adjacency.get(n1, set()))
                if n1 < n2
            ],
            "all_resources": self.all_resources(),
        }
