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
nabor7/
├── main.py             # Entry point (Menu Interativo CLI)
├── README.md           # Documentação
├── simulator/
│   ├── __init__.py
│   ├── network.py      # Classe P2PNetwork (carregamento e validação)
│   └── algorithms.py   # Os 4 algoritmos de busca (flooding, etc)
└── examples/           # Redes de exemplo em JSON prontas para testar
```
