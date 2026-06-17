# Simulador de Busca em Redes P2P

**Trabalho 7 – Computação Distribuída**  
Prof. Nabor C. Mendonça

---

## Integrantes

| Nome | Matrícula |
|------|-----------|
| Pedro Diógenes | 2315029 |
| Matheus Vasconcelos | 2315043 |
| Erich Lima | 2310362 |
| Rebeca Vicente | 2122489 |

## Visão Geral

Simulador de algoritmos de busca em redes P2P não estruturadas, acessível inteiramente por linha de comando (CLI).

**Algoritmos implementados:**
| Algoritmo | Descrição |
|-----------|-----------|
| `flooding` | Inundação pura: query enviada a *todos* os vizinhos, decrementando TTL |
| `informed_flooding` | Inundação com cache: nós verificam o cache antes de propagar |
| `random_walk` | Passeio aleatório: query enviada a *um* vizinho escolhido aleatoriamente |
| `informed_random_walk` | Passeio aleatório com cache: idem, verificando o cache em cada nó |

---

## Requisitos

- **Python 3.10+**
- **matplotlib** e **networkx** (para visualização gráfica e animação)

```bash
pip install matplotlib networkx
```

---

## Como Executar

Como o simulador é um console interativo, rode o script da seguinte forma:

```bash
# Inicia o simulador e abre o menu interativo no seu terminal
python main.py
```

Ou, se quiser passar todos os parâmetros de uma vez para rodar testes rápidos sem menu:
```bash
python main.py examples/network_small.json n1 r9 --algo flooding --ttl 10
```

Flags opcionais disponíveis no modo direto:

| Flag | Efeito |
|------|--------|
| `--historico` | Exibe o histórico passo a passo no terminal (QUERY, CHECK, DUPLIC, ACHOU, etc.) |
| `--grafico` | Exibe o grafo da rede com cores indicando o caminho percorrido |
| `--animar` | Exibe a animação frame a frame da busca com histórico ao vivo |

Exemplo combinado:
```bash
python main.py examples/network_small.json n1 r9 --algo flooding --ttl 10 --historico --grafico --animar
```

No **modo interativo**, o programa pergunta se deseja ver o histórico, o grafo e a animação após cada busca, além de oferecer o **modo comparativo** (opção `2`) que roda os 4 algoritmos e exibe tabela + gráfico de barras.

---

## Formato do Arquivo de Configuração (JSON)

```json
{
  "num_nodes": 12,
  "min_neighbors": 2,
  "max_neighbors": 4,
  "resources": {
    "n1": ["r1", "r2", "r3"],
    "n2": ["r4", "r5"]
  },
  "edges": [
    ["n1", "n2"],
    ["n1", "n3"],
    ["n2", "n4"]
  ]
}
```

---

## Validações (Requisitos II)

Ao carregar um arquivo, o simulador verifica automaticamente:

1. `num_nodes` bate com a quantidade real de nós definidos
2. Sem arestas de loop (um nó conectado a si mesmo)
3. Nenhum nó sem recursos
4. O grau de cada nó respeita `min_neighbors` e `max_neighbors`
5. A rede é conexa (sem partições)

Se alguma regra for violada, os erros são exibidos no terminal e o sistema pede para você carregar um arquivo válido.

---

## Estrutura do Projeto

```text
NaborTrabalho7/
├── main.py             # Entry point (menu interativo + modo direto com flags)
├── README.md           # Documentação
├── simulator/
│   ├── __init__.py
│   ├── network.py      # Classe P2PNetwork (carregamento e validação)
│   ├── algorithms.py   # Os 4 algoritmos de busca
│   ├── visualizer.py   # Grafo estático e animação (matplotlib + networkx)
│   └── stats.py        # Comparativo dos 4 algoritmos (tabela + gráfico)
└── examples/           # Redes de exemplo em JSON prontas para testar
    ├── network_small.json               # 6 nós (válido)
    ├── network_medium.json              # 12 nós (válido)
    ├── network_large.json               # 20 nós (válido)
    ├── network_invalid_degree.json      # Viola min/max vizinhos
    ├── network_invalid_loop.json        # Self-loop
    ├── network_invalid_no_resources.json# Nó sem recursos
    └── network_invalid_partitioned.json # Rede particionada
```
