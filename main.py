#!/usr/bin/env python3
"""
main.py - Simulador de Busca em Redes P2P (CLI)
Trabalho 7 - Computacao Distribuida

Uso interativo:
  python main.py

Uso com argumentos (para testes rapidos):
  python main.py examples/network_small.json n1 r9 --algo flooding --ttl 10
"""

import sys
import argparse
from simulator.network import P2PNetwork, ValidationError

def print_header():
    print("\n" + "="*60)
    print("  SIMULADOR DE BUSCA EM REDES P2P - MODO TERMINAL")
    print("  Computacao Distribuida - Prof. Nabor C. Mendonca")
    print("="*60 + "\n")

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
        
        node_id = input("Nó inicial (ex: n1): ").strip()
        if not node_id: break
        if node_id not in net.nodes:
            print(f"  -> Nó '{node_id}' nao existe na rede.")
            continue
            
        resource_id = input("Recurso buscado (ex: r9): ").strip()
        if not resource_id: break
        
        try:
            ttl = int(input("TTL (ex: 10): ").strip() or "10")
        except ValueError:
            print("  -> TTL deve ser um numero inteiro.")
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

        print(f"\n>> Executando {algo.upper()} a partir do no {node_id} buscando {resource_id} (TTL={ttl})...")
        
        # 3. Executar e mostrar resultados
        try:
            result = net.search(node_id, resource_id, ttl, algo)
            
            print("\n--- RESULTADO DA BUSCA ---")
            if result.found:
                print(f"  Status:         ENCONTRADO")
                print(f"  Encontrado em:  {result.found_at}")
            else:
                print(f"  Status:         NAO ENCONTRADO (TTL esgotado)")
                
            print(f"  Mensagens:      {result.messages}")
            print(f"  Nos visitados:  {result.nodes_visited}")
            
        except Exception as e:
            print(f"  [ERRO] Falha na busca: {e}")
            
        print()

def cli_mode(args):
    """Executa a busca direto via argumentos (bom para testar rapido)"""
    try:
        net = P2PNetwork.load_from_file(args.config)
        net.validate()
    except Exception as e:
        print(f"Erro ao carregar rede: {e}")
        return

    try:
        result = net.search(args.node, args.resource, args.ttl, args.algo)
        print(f"\nAlgoritmo: {args.algo}")
        print(f"Encontrado: {result.found} " + (f"(em {result.found_at})" if result.found else ""))
        print(f"Mensagens enviadas: {result.messages}")
        print(f"Nos visitados: {result.nodes_visited}\n")
    except Exception as e:
        print(f"Erro na busca: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador de Busca em Redes P2P")
    parser.add_argument("config", nargs="?", help="Arquivo JSON da rede")
    parser.add_argument("node", nargs="?", help="Nó inicial")
    parser.add_argument("resource", nargs="?", help="Recurso buscado")
    parser.add_argument("--algo", default="flooding", choices=["flooding", "informed_flooding", "random_walk", "informed_random_walk"])
    parser.add_argument("--ttl", type=int, default=10)
    
    args = parser.parse_args()
    
    # Se passou todos os 3 argumentos principais, roda direto
    if args.config and args.node and args.resource:
        cli_mode(args)
    else:
        # Senao roda o modo interativo
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print("\nSaindo...")
            sys.exit(0)
