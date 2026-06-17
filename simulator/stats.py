"""
stats.py – Estatísticas comparativas entre os 4 algoritmos de busca.

Executa todos os algoritmos para o mesmo cenário e exibe:
  • Tabela no terminal
  • Gráfico de barras comparativo (matplotlib)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


ALGOS = ["flooding", "informed_flooding", "random_walk", "informed_random_walk"]

ALGO_LABELS = {
    "flooding":             "Flooding",
    "informed_flooding":    "Inf. Flooding",
    "random_walk":          "Random Walk",
    "informed_random_walk": "Inf. R. Walk",
}

ALGO_COLORS = {
    "flooding":             "#4a90d9",
    "informed_flooding":    "#27ae60",
    "random_walk":          "#e67e22",
    "informed_random_walk": "#9b59b6",
}


# ======================================================================
# Coleta de resultados
# ======================================================================

def run_all(network, node_id: str, resource_id: str, ttl: int) -> dict:
    """
    Executa os 4 algoritmos para o mesmo cenário.
    Reseta o cache antes de cada execução para garantir comparação justa.
    Retorna dict {algo: SearchResult}.
    """
    results = {}
    for algo in ALGOS:
        network.reset_cache()
        results[algo] = network.search(node_id, resource_id, ttl, algo)
    network.reset_cache()
    return results


# ======================================================================
# Tabela no terminal
# ======================================================================

def print_stats_table(results: dict, node_id: str, resource_id: str, ttl: int):
    """Imprime tabela comparativa no terminal."""
    col_w = [20, 12, 14, 12]
    sep = "+" + "+".join("-" * w for w in col_w) + "+"

    def row(cells):
        return "|" + "|".join(f" {str(c):<{w-1}}" for c, w in zip(cells, col_w)) + "|"

    print(f"\n{'='*62}")
    print(f"  COMPARATIVO — no: {node_id}  |  recurso: {resource_id}  |  TTL={ttl}")
    print(f"{'='*62}")
    print(sep)
    print(row(["Algoritmo", "Encontrado", "Mensagens", "Nos Visit."]))
    print(sep)
    for algo in ALGOS:
        r = results[algo]
        encontrado = "SIM (" + r.found_at + ")" if r.found else "NAO"
        print(row([ALGO_LABELS[algo], encontrado, r.messages, r.nodes_visited]))
    print(sep)

    # Destaque do melhor em mensagens (entre os que encontraram)
    found_algos = [a for a in ALGOS if results[a].found]
    if found_algos:
        best = min(found_algos, key=lambda a: results[a].messages)
        print(f"\n  Menor numero de mensagens (entre os que encontraram): "
              f"{ALGO_LABELS[best]} ({results[best].messages} msgs)")
    print()


# ======================================================================
# Gráfico comparativo
# ======================================================================

def show_stats_chart(results: dict, node_id: str, resource_id: str, ttl: int):
    """Exibe gráfico de barras comparando mensagens e nós visitados."""
    labels  = [ALGO_LABELS[a] for a in ALGOS]
    msgs    = [results[a].messages      for a in ALGOS]
    visited = [results[a].nodes_visited for a in ALGOS]
    colors  = [ALGO_COLORS[a]           for a in ALGOS]

    x = np.arange(len(ALGOS))
    width = 0.38

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    bars_msg = ax.bar(x - width/2, msgs,    width, color=colors, alpha=0.9, label="Mensagens")
    bars_vis = ax.bar(x + width/2, visited, width, color=colors, alpha=0.45, label="Nos visitados",
                      edgecolor=colors, linewidth=1.5)

    # Valores em cima das barras
    for bar in bars_msg:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
                str(int(bar.get_height())), ha="center", va="bottom",
                color="white", fontsize=10, fontweight="bold")
    for bar in bars_vis:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
                str(int(bar.get_height())), ha="center", va="bottom",
                color="white", fontsize=10)

    # Marca nao encontrado
    for i, algo in enumerate(ALGOS):
        if not results[algo].found:
            ax.text(x[i], max(msgs + visited) * 0.5, "NAO\nENCONTRADO",
                    ha="center", va="center", color="#e74c3c",
                    fontsize=9, fontweight="bold",
                    bbox=dict(facecolor="#1e1e2e", edgecolor="#e74c3c", boxstyle="round,pad=0.3"))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, color="white", fontsize=11)
    ax.tick_params(axis="y", colors="white")
    ax.spines["bottom"].set_color("#555577")
    ax.spines["left"].set_color("#555577")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_tick_params(labelcolor="white")
    ax.set_ylabel("Quantidade", color="white", fontsize=11)
    ax.set_title(
        f"Comparativo de Algoritmos  —  início: {node_id}  |  "
        f"recurso: {resource_id}  |  TTL={ttl}",
        color="white", fontsize=12, pad=14
    )

    # Legenda manual
    legend_items = [
        mpatches.Patch(facecolor="white", alpha=0.9, label="Barras cheias = Mensagens"),
        mpatches.Patch(facecolor="white", alpha=0.35, label="Barras claras = Nos visitados"),
    ]
    ax.legend(handles=legend_items, facecolor="#2a2a3e", labelcolor="white",
              fontsize=9, framealpha=0.85, loc="upper right")

    plt.tight_layout()
    plt.show()
