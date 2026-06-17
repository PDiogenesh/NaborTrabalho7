#!/usr/bin/env python3
"""
main.py - Simulador de Busca em Redes P2P (CLI)
Trabalho 7 - Computacao Distribuida

Uso interativo:
  python main.py

Uso com argumentos (para testes rapidos):
  python main.py examples/network_small.json n1 r9 --algo flooding --ttl 10
  python main.py examples/network_small.json n1 r9 --algo flooding --ttl 10 --historico
"""

import sys
import argparse
from simulator.network import P2PNetwork, ValidationError
from simulator.visualizer import show_network, show_search, animate_search
from simulator.stats import run_all, print_stats_table, show_stats_chart


def print_header():
    print("\n" + "="*60)
    print("  SIMULADOR DE BUSCA EM REDES P2P - MODO TERMINAL")
    print("  Computacao Distribuida - Prof. Nabor C. Mendonca")
    print("="*60 + "\n")


def print_historico(steps: list):
    """Imprime o histórico passo a passo da busca a partir dos steps."""
    print("\n--- HISTORICO DA BUSCA ---")
    msg_num = 0
    for step in steps:
        t = step.get("type")

        if t == "query":
            msg_num += 1
            ttl_str = f"  TTL={step['ttl']}" if "ttl" in step else ""
            direct = "  [DIRETO via cache]" if step.get("direct") else ""
            print(f"  [{msg_num:02d}] QUERY    {step['from']} --> {step['to']}   (buscando {step['resource']}){ttl_str}{direct}")

        elif t == "check":
            status = "TEM" if step["found"] else "nao tem"
            print(f"       CHECK    {step['node']} {status} '{step['resource']}'")

        elif t == "cache_hit":
            print(f"       CACHE    {step['node']} sabe que '{step['resource']}' esta em {step['cached_at']}")

        elif t == "duplicate":
            print(f"       DUPLIC   {step['node']} ja recebeu esta query (de {step['from']}) - descartada")

        elif t == "found":
            local = " (recurso local)" if step.get("local") else ""
            cache = " (via cache)" if step.get("from_cache") else ""
            print(f"       ACHOU    '{step['resource']}' encontrado em {step['node']}{local}{cache}")

        elif t == "response":
            msg_num += 1
            cache = "  [INFO de cache]" if step.get("from_cache") else ""
            found_at = f" -> recurso esta em {step['found_at']}" if step.get("found_at") else ""
            print(f"  [{msg_num:02d}] RESPOSTA {step['from']} --> {step['to']}{found_at}{cache}")

        elif t == "ttl_expired":
            print(f"       TTL=0    {step['node']} - query descartada")

        elif t == "not_found":
            print(f"       FIM      '{step['resource']}' nao encontrado (TTL esgotado)")

    print()


def print_resultado(result):
    print("\n--- RESULTADO DA BUSCA ---")
    if result.found:
        print(f"  Status:         ENCONTRADO")
        print(f"  Encontrado em:  {result.found_at}")
    else:
        print(f"  Status:         NAO ENCONTRADO (TTL esgotado)")
    print(f"  Mensagens:      {result.messages}")
    print(f"  Nos visitados:  {result.nodes_visited}")


def interactive_mode():
    print_header()

    # 1. Carregar arquivo
    net = None
    while not net:
        filepath = input("Digite o caminho do arquivo JSON da rede (ex: examples/network_small.json): ").strip()
        if not filepath:
            print("  Saindo...")
            return

        try:
            net = P2PNetwork.load_from_file(filepath)
            net.validate()
            print(f"\n  [OK] Rede carregada com sucesso!")
            print(f"       Nos: {net.num_nodes} | Recursos totais: {len(net.all_resources())}")
            print(f"       Vizinhos exigidos: min {net.min_neighbors}, max {net.max_neighbors}\n")
            ver_grafo = input("  Exibir grafo da rede? (s/N): ").strip().lower()
            if ver_grafo == "s":
                show_network(net)
        except FileNotFoundError:
            print(f"  [ERRO] Arquivo '{filepath}' nao encontrado.")
            net = None
        except ValidationError as e:
            print("\n  [FALHA NA VALIDACAO] A rede nao atende aos requisitos:")
            for err in e.errors:
                print(f"    - {err}")
            print("  Por favor, carregue um arquivo valido.\n")
            net = None
        except Exception as e:
            print(f"  [ERRO] Falha ao ler arquivo: {e}")
            net = None

    # 2. Menu de buscas
    while True:
        print("-" * 60)
        print("NOVA BUSCA (ou pressione Enter vazio para sair)")

        node_id = input("No inicial (ex: n1): ").strip()
        if not node_id:
            break
        if node_id not in net.nodes:
            print(f"  -> No '{node_id}' nao existe na rede.")
            continue

        resource_id = input("Recurso buscado (ex: r9): ").strip()
        if not resource_id:
            break

        try:
            ttl = int(input("TTL (ex: 10): ").strip() or "10")
        except ValueError:
            print("  -> TTL deve ser um numero inteiro.")
            continue

        print("\nModo:")
        print("  1 - Busca individual (escolhe o algoritmo)")
        print("  2 - Comparativo (roda os 4 algoritmos e exibe estatisticas)")
        modo = input("Escolha (1/2) [padrao: 1]: ").strip()

        if modo == "2":
            print(f"\n>> Rodando os 4 algoritmos a partir de {node_id} buscando {resource_id} (TTL={ttl})...")
            try:
                results = run_all(net, node_id, resource_id, ttl)
                print_stats_table(results, node_id, resource_id, ttl)
                ver_chart = input("  Exibir grafico comparativo? (s/N): ").strip().lower()
                if ver_chart == "s":
                    show_stats_chart(results, node_id, resource_id, ttl)
            except Exception as e:
                print(f"  [ERRO] Falha nas buscas: {e}")
            print()
            continue

        print("\nAlgoritmos:")
        print("  1 - flooding")
        print("  2 - informed_flooding (usa cache)")
        print("  3 - random_walk")
        print("  4 - informed_random_walk (usa cache)")

        algo_choice = input("Escolha (1-4) [padrao: 1]: ").strip()
        algo_map = {
            "1": "flooding", "2": "informed_flooding",
            "3": "random_walk", "4": "informed_random_walk"
        }
        algo = algo_map.get(algo_choice, "flooding")

        mostrar_hist = input("Mostrar historico passo a passo? (s/N): ").strip().lower()

        print(f"\n>> Executando {algo.upper()} a partir do no {node_id} buscando {resource_id} (TTL={ttl})...")

        try:
            result = net.search(node_id, resource_id, ttl, algo)

            if mostrar_hist == "s":
                print_historico(result.steps)

            print_resultado(result)

            ver_resultado = input("  Exibir grafo do resultado? (s/N): ").strip().lower()
            if ver_resultado == "s":
                show_search(net, result)

            ver_anim = input("  Exibir animacao passo a passo? (s/N): ").strip().lower()
            if ver_anim == "s":
                try:
                    velocidade = input("  Velocidade (1=lenta, 2=normal, 3=rapida) [padrao: 2]: ").strip()
                    intervalos = {"1": 1400, "2": 900, "3": 400}
                    intervalo = intervalos.get(velocidade, 900)
                    animate_search(net, result, interval=intervalo)
                except Exception as e:
                    print(f"  [ERRO] Falha na animacao: {e}")

        except Exception as e:
            print(f"  [ERRO] Falha na busca: {e}")

        print()


def cli_mode(args):
    """Executa a busca direto via argumentos (bom para testar rapido)."""
    try:
        net = P2PNetwork.load_from_file(args.config)
        net.validate()
    except Exception as e:
        print(f"Erro ao carregar rede: {e}")
        return

    try:
        result = net.search(args.node, args.resource, args.ttl, args.algo)

        if args.historico:
            print_historico(result.steps)

        print(f"\nAlgoritmo: {args.algo}")
        print(f"Encontrado: {result.found} " + (f"(em {result.found_at})" if result.found else ""))
        print(f"Mensagens enviadas: {result.messages}")
        print(f"Nos visitados: {result.nodes_visited}\n")

        if args.grafico:
            show_search(net, result)

        if args.animar:
            animate_search(net, result)
    except Exception as e:
        print(f"Erro na busca: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador de Busca em Redes P2P")
    parser.add_argument("config", nargs="?", help="Arquivo JSON da rede")
    parser.add_argument("node", nargs="?", help="No inicial")
    parser.add_argument("resource", nargs="?", help="Recurso buscado")
    parser.add_argument("--algo", default="flooding",
                        choices=["flooding", "informed_flooding", "random_walk", "informed_random_walk"])
    parser.add_argument("--ttl", type=int, default=10)
    parser.add_argument("--historico", action="store_true",
                        help="Exibe o historico passo a passo da busca")
    parser.add_argument("--grafico", action="store_true",
                        help="Exibe o grafo visual do resultado da busca")
    parser.add_argument("--animar", action="store_true",
                        help="Exibe a animacao passo a passo da busca")

    args = parser.parse_args()

    if args.config and args.node and args.resource:
        cli_mode(args)
    else:
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print("\nSaindo...")
            sys.exit(0)
