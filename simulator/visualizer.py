"""
visualizer.py – Visualização gráfica da rede P2P e resultado de buscas.

Três funções principais:
  • show_network(network)          — exibe a rede carregada do JSON
  • show_search(network, result)   — exibe a rede destacando o caminho da busca
  • animate_search(network, result)— animação passo a passo da busca
"""

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation


# ======================================================================
# Helpers internos
# ======================================================================

def _build_graph(network) -> nx.Graph:
    G = nx.Graph()
    for node in network.nodes:
        resources = ", ".join(network.resources.get(node, []))
        G.add_node(node, resources=resources)
    for n1 in network.nodes:
        for n2 in network.adjacency.get(n1, set()):
            if n1 < n2:
                G.add_edge(n1, n2)
    return G


def _node_label(node: str, network) -> str:
    resources = network.resources.get(node, [])
    res_str = "\n".join(resources)
    return f"{node}\n{res_str}"


# ======================================================================
# 1. Visualização da rede original
# ======================================================================

def show_network(network):
    """Exibe a rede P2P carregada do JSON com nós e recursos."""
    G = _build_graph(network)
    pos = nx.spring_layout(G, seed=42, k=2.5)

    labels = {node: _node_label(node, network) for node in G.nodes()}

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")
    ax.set_title(
        f"Rede P2P  —  {network.num_nodes} nós  |  "
        f"vizinhos: [{network.min_neighbors}, {network.max_neighbors}]  |  "
        f"{len(network.all_resources())} recursos",
        color="white", fontsize=13, pad=14
    )

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#555577", width=1.8, alpha=0.7)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#4a90d9", node_size=1600, alpha=0.95)
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_color="white", font_size=7.5, font_weight="bold")

    ax.axis("off")
    plt.tight_layout()
    plt.show()


# ======================================================================
# 2. Visualização do resultado de uma busca
# ======================================================================

def show_search(network, result):
    """
    Exibe a rede destacando os nós e arestas envolvidos na busca.

    Legenda de cores dos nós:
      Azul escuro  — nó inicial
      Verde        — nó onde o recurso foi encontrado
      Laranja      — nós visitados durante a busca
      Cinza        — nós não visitados
    """
    G = _build_graph(network)
    pos = nx.spring_layout(G, seed=42, k=2.5)

    # Extrai nós e arestas visitados a partir dos steps
    visited_nodes = set()
    visited_edges = set()
    duplicate_edges = set()

    for step in result.steps:
        t = step.get("type")
        if t == "query":
            visited_nodes.add(step["from"])
            visited_nodes.add(step["to"])
            e = tuple(sorted([step["from"], step["to"]]))
            visited_edges.add(e)
        elif t == "duplicate":
            visited_nodes.add(step["node"])
            e = tuple(sorted([step["from"], step["node"]]))
            duplicate_edges.add(e)
        elif t in ("check", "cache_hit", "found", "ttl_expired"):
            visited_nodes.add(step["node"])
        elif t == "response":
            visited_nodes.add(step["from"])
            visited_nodes.add(step["to"])

    # Cores dos nós
    node_colors = []
    for node in G.nodes():
        if node == result.start_node:
            node_colors.append("#2255cc")       # azul escuro — origem
        elif node == result.found_at:
            node_colors.append("#27ae60")       # verde — encontrado
        elif node in visited_nodes:
            node_colors.append("#e67e22")       # laranja — visitado
        else:
            node_colors.append("#555566")       # cinza — não visitado

    # Cores das arestas
    all_edges = list(G.edges())
    edge_colors = []
    edge_widths = []
    for e in all_edges:
        key = tuple(sorted(e))
        if key in visited_edges:
            edge_colors.append("#e67e22")
            edge_widths.append(3.0)
        elif key in duplicate_edges:
            edge_colors.append("#c0392b")
            edge_widths.append(2.0)
        else:
            edge_colors.append("#333344")
            edge_widths.append(1.2)

    labels = {node: _node_label(node, network) for node in G.nodes()}

    status = "ENCONTRADO" if result.found else "NAO ENCONTRADO"
    found_info = f"em {result.found_at}" if result.found else "TTL esgotado"
    title = (
        f"{result.algo.upper()}  |  início: {result.start_node}  |  "
        f"buscando: {result.resource}  |  TTL={result.ttl}\n"
        f"{status} ({found_info})  —  "
        f"{result.messages} mensagens  |  {result.nodes_visited} nós visitados"
    )

    fig, ax = plt.subplots(figsize=(13, 8))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")
    ax.set_title(title, color="white", fontsize=11, pad=14)

    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=all_edges,
                           edge_color=edge_colors, width=edge_widths, alpha=0.85)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=1600, alpha=0.95)
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_color="white", font_size=7.5, font_weight="bold")

    # Legenda
    legend_items = [
        mpatches.Patch(color="#2255cc", label=f"Origem ({result.start_node})"),
        mpatches.Patch(color="#27ae60", label=f"Encontrado ({result.found_at})") if result.found
            else mpatches.Patch(color="#555566", label="Não encontrado"),
        mpatches.Patch(color="#e67e22", label="Nó visitado"),
        mpatches.Patch(color="#555566", label="Nó não visitado"),
        mpatches.Patch(color="#e67e22", label="Aresta percorrida"),
        mpatches.Patch(color="#c0392b", label="Mensagem duplicada"),
    ]
    ax.legend(handles=legend_items, loc="upper left", facecolor="#2a2a3e",
              labelcolor="white", fontsize=9, framealpha=0.85)

    ax.axis("off")
    plt.tight_layout()
    plt.show()


# ======================================================================
# 3. Animação passo a passo da busca
# ======================================================================

def animate_search(network, result, interval: int = 900):
    """
    Anima a busca passo a passo: cada frame corresponde a um evento
    (query, check, cache_hit, duplicate, found, response, ttl_expired).

    interval: tempo em ms entre frames (padrão 900ms).
    """
    G = _build_graph(network)
    pos = nx.spring_layout(G, seed=42, k=2.5)
    all_nodes = sorted(G.nodes())
    all_edges = list(G.edges())
    labels = {node: _node_label(node, network) for node in G.nodes()}

    anim_steps = [s for s in result.steps if s.get("type") not in ("not_found",)]

    def build_frames():
        visited_nodes = set()
        active_node = None
        active_edge = None
        found_node = None
        duplicate_edges = set()
        visited_edges = set()
        response_edges = set()
        log_lines = []
        msg_count = 0
        frames = []

        for step in anim_steps:
            t = step.get("type")
            active_node = None
            active_edge = None

            if t == "query":
                msg_count += 1
                visited_nodes.add(step["from"])
                visited_nodes.add(step["to"])
                active_edge = tuple(sorted([step["from"], step["to"]]))
                visited_edges.add(active_edge)
                direct = " [DIRETO via cache]" if step.get("direct") else ""
                log_lines.append(
                    f"[{msg_count:02d}] QUERY  {step['from']} --> {step['to']}"
                    f"  TTL={step.get('ttl', '?')}{direct}"
                )

            elif t == "check":
                active_node = step["node"]
                visited_nodes.add(step["node"])
                status = "TEM" if step["found"] else "nao tem"
                log_lines.append(f"      CHECK  {step['node']} {status} '{step['resource']}'")

            elif t == "cache_hit":
                active_node = step["node"]
                visited_nodes.add(step["node"])
                log_lines.append(
                    f"      CACHE  {step['node']} sabe: '{step['resource']}' esta em {step['cached_at']}"
                )

            elif t == "duplicate":
                active_node = step["node"]
                visited_nodes.add(step["node"])
                e = tuple(sorted([step["from"], step["node"]]))
                duplicate_edges.add(e)
                log_lines.append(f"      DUPLIC {step['node']} ja recebeu (de {step['from']})")

            elif t == "found":
                found_node = step["node"]
                active_node = step["node"]
                visited_nodes.add(step["node"])
                local = " (local)" if step.get("local") else ""
                cache = " (cache)" if step.get("from_cache") else ""
                log_lines.append(f"   ** ACHOU  '{step['resource']}' em {step['node']}{local}{cache} **")

            elif t == "response":
                msg_count += 1
                visited_nodes.add(step["from"])
                visited_nodes.add(step["to"])
                active_edge = tuple(sorted([step["from"], step["to"]]))
                response_edges.add(active_edge)
                cache = " [cache]" if step.get("from_cache") else ""
                log_lines.append(f"[{msg_count:02d}] RESP   {step['from']} --> {step['to']}{cache}")

            elif t == "ttl_expired":
                active_node = step["node"]
                visited_nodes.add(step["node"])
                log_lines.append(f"      TTL=0  {step['node']} descartado")

            frames.append({
                "visited_nodes":   set(visited_nodes),
                "active_node":     active_node,
                "active_edge":     active_edge,
                "found_node":      found_node,
                "visited_edges":   set(visited_edges),
                "duplicate_edges": set(duplicate_edges),
                "response_edges":  set(response_edges),
                "log":             list(log_lines[-12:]),
                "msg_count":       msg_count,
            })

        return frames

    frames = build_frames()
    if not frames:
        print("  [AVISO] Nenhum passo para animar.")
        return

    fig, (ax_graph, ax_log) = plt.subplots(
        1, 2, figsize=(15, 7),
        gridspec_kw={"width_ratios": [2, 1]}
    )
    fig.patch.set_facecolor("#1e1e2e")
    ax_graph.set_facecolor("#1e1e2e")
    ax_log.set_facecolor("#12121f")

    status_str = "ENCONTRADO" if result.found else "NAO ENCONTRADO"
    found_info = f"em {result.found_at}" if result.found else "TTL esgotado"
    fig.suptitle(
        f"{result.algo.upper()}  |  início: {result.start_node}  |  "
        f"buscando: {result.resource}  |  TTL={result.ttl}  —  {status_str} ({found_info})",
        color="white", fontsize=11
    )

    legend_items = [
        mpatches.Patch(color="#2255cc", label=f"Origem ({result.start_node})"),
        mpatches.Patch(color="#27ae60", label="Encontrado"),
        mpatches.Patch(color="#ff4444", label="Ativo agora"),
        mpatches.Patch(color="#e67e22", label="Visitado"),
        mpatches.Patch(color="#555566", label="Nao visitado"),
        mpatches.Patch(color="#c0392b", label="Duplicata"),
        mpatches.Patch(color="#1abc9c", label="Resposta"),
    ]

    def draw_frame(frame_idx):
        ax_graph.clear()
        ax_graph.set_facecolor("#1e1e2e")
        ax_graph.axis("off")
        ax_graph.legend(handles=legend_items, loc="upper left", facecolor="#2a2a3e",
                        labelcolor="white", fontsize=8, framealpha=0.85)

        f = frames[frame_idx]

        node_colors = []
        node_sizes = []
        for node in all_nodes:
            if node == f["active_node"]:
                node_colors.append("#ff4444")
                node_sizes.append(2200)
            elif node == f["found_node"]:
                node_colors.append("#27ae60")
                node_sizes.append(1900)
            elif node == result.start_node:
                node_colors.append("#2255cc")
                node_sizes.append(1800)
            elif node in f["visited_nodes"]:
                node_colors.append("#e67e22")
                node_sizes.append(1600)
            else:
                node_colors.append("#555566")
                node_sizes.append(1400)

        edge_colors = []
        edge_widths = []
        for e in all_edges:
            key = tuple(sorted(e))
            if key == f["active_edge"]:
                edge_colors.append("#ff4444")
                edge_widths.append(4.5)
            elif key in f["response_edges"]:
                edge_colors.append("#1abc9c")
                edge_widths.append(3.0)
            elif key in f["duplicate_edges"]:
                edge_colors.append("#c0392b")
                edge_widths.append(2.0)
            elif key in f["visited_edges"]:
                edge_colors.append("#e67e22")
                edge_widths.append(2.5)
            else:
                edge_colors.append("#333344")
                edge_widths.append(1.2)

        nx.draw_networkx_edges(G, pos, ax=ax_graph, edgelist=all_edges,
                               edge_color=edge_colors, width=edge_widths, alpha=0.9)
        nx.draw_networkx_nodes(G, pos, ax=ax_graph, nodelist=all_nodes,
                               node_color=node_colors, node_size=node_sizes, alpha=0.95)
        nx.draw_networkx_labels(G, pos, labels=labels, ax=ax_graph,
                                font_color="white", font_size=7.5, font_weight="bold")

        ax_graph.set_title(
            f"Passo {frame_idx + 1}/{len(frames)}  |  Mensagens: {f['msg_count']}",
            color="white", fontsize=10
        )

        ax_log.clear()
        ax_log.set_facecolor("#12121f")
        ax_log.axis("off")
        ax_log.set_title("Historico", color="white", fontsize=10)
        log_text = "\n".join(f["log"])
        ax_log.text(0.03, 0.97, log_text, transform=ax_log.transAxes,
                    color="#dddddd", fontsize=8.5, verticalalignment="top",
                    fontfamily="monospace",
                    bbox=dict(facecolor="#1a1a2e", edgecolor="#444466",
                              boxstyle="round,pad=0.5", alpha=0.9))

    anim = animation.FuncAnimation(
        fig,
        draw_frame,
        frames=len(frames),
        interval=interval,
        repeat=False,
    )

    plt.tight_layout()
    plt.show()
    return anim
