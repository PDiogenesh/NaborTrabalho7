# Progresso – Trabalho 7: Simulador de Busca em Redes P2P

**Disciplina:** Computação Distribuída – Prof. Nabor C. Mendonça  
**Status geral:** COMPLETO ✅

---

## Integrantes

| Nome | Matrícula |
|---|---|
| Pedro Diógenes | 2315029 |
| Matheus Vasconcelos | 2315043 |
| Erich Lima | 2310362 |
| Rebeca Vicente | 2122489 |

---

## Estrutura do Projeto

```
NaborTrabalho7/
├── main.py                          # Entry point (CLI interativo + modo direto)
├── simulator/
│   ├── __init__.py
│   ├── network.py                   # Classe P2PNetwork: carregamento e validação
│   ├── algorithms.py                # 4 algoritmos de busca
│   ├── visualizer.py                # Grafo estático + animação (matplotlib/networkx)
│   └── stats.py                     # Estatísticas comparativas
└── examples/
    ├── network_small.json            # 6 nós (válido)
    ├── network_medium.json           # 12 nós (válido)
    ├── network_large.json            # 20 nós (válido)
    ├── network_invalid_degree.json   # Viola min/max vizinhos
    ├── network_invalid_loop.json     # Aresta de nó para si mesmo
    ├── network_invalid_no_resources.json  # Nó sem recursos
    └── network_invalid_partitioned.json   # Rede particionada
```

---

## O que foi implementado

### 1. Carregamento e validação da rede (`network.py`)

Lê um arquivo JSON com a topologia da rede e valida 5 regras:

| Regra | Descrição |
|---|---|
| 1 | `num_nodes` bate com a contagem real de nós |
| 2 | Sem arestas de loop (nó conectado a si mesmo) |
| 3 | Nenhum nó sem recursos |
| 4 | Grau de cada nó respeita `min_neighbors` e `max_neighbors` |
| 5 | Rede conexa (sem partições) |

Se alguma regra for violada, todos os erros são listados de uma vez no terminal.

---

### 2. Algoritmos de busca (`algorithms.py`)

Quatro algoritmos implementados, todos com contagem de mensagens e log de passos (`steps`):

#### `flooding` — Inundação real (comportamento P2P correto)
- Cada nó envia a query para **todos** os seus vizinhos sem saber o que os outros já fizeram
- Mensagens redundantes são **contadas** (enviadas em paralelo)
- Quando o recurso é encontrado, os ramos já despachados continuam sendo processados e contados
- Um nó descarta queries repetidas, mas a mensagem já foi contada

#### `informed_flooding` — Inundação com cache
- Igual ao flooding real, mas cada nó consulta seu **cache local** antes de propagar
- Se o cache indica onde o recurso está, responde diretamente sem propagar mais
- Cache é atualizado quando um recurso é encontrado

#### `random_walk` — Passeio aleatório puro ("burro")
- Envia a query para **um único vizinho**, escolhido **completamente ao acaso**
- Sem heurística de evitar o nó anterior — pode voltar, pode revisitar
- Continua até encontrar o recurso ou o TTL zerar

#### `informed_random_walk` — Passeio aleatório com cache
- Igual ao random_walk, mas consulta o cache em cada nó visitado
- Se encontrar no cache, responde diretamente sem continuar o passeio

**Métricas retornadas por cada busca:**
- `found` — se o recurso foi encontrado
- `found_at` — nó onde foi encontrado
- `messages` — total de mensagens trocadas
- `nodes_visited` — total de nós envolvidos
- `steps` — log detalhado de cada evento (usado pelo histórico e animação)

---

### 3. Histórico passo a passo no terminal (`main.py`)

Após cada busca, o programa pode exibir o histórico completo evento a evento:

```
[01] QUERY    n1 --> n2   (buscando r9)  TTL=4
     CHECK    n2 nao tem 'r9'
[02] QUERY    n2 --> n3   (buscando r9)  TTL=3
     DUPLIC   n3 ja recebeu esta query (de n2) - descartada
     CHECK    n6 TEM 'r9'
     ACHOU    'r9' encontrado em n6
[11] RESPOSTA n6 --> n1
```

Eventos exibidos: `QUERY`, `CHECK`, `CACHE`, `DUPLIC`, `ACHOU`, `RESPOSTA`, `TTL=0`

**Ativar:**
- Modo interativo: pergunta `"Mostrar historico passo a passo? (s/N)"`
- Modo CLI: flag `--historico`

---

### 4. Visualização gráfica (`visualizer.py`)

#### Grafo da rede (`show_network`)
- Exibe a topologia completa com nós, recursos e arestas
- Fundo escuro, nós azuis, labels com ID e recursos

#### Grafo do resultado (`show_search`)
Exibe a rede após a busca com código de cores:

| Cor | Significado |
|---|---|
| Azul escuro | Nó de origem |
| Verde | Nó onde o recurso foi encontrado |
| Laranja | Nós e arestas visitados |
| Vermelho escuro | Arestas com mensagens duplicadas |
| Cinza | Nós não visitados |

**Ativar:**
- Modo interativo: pergunta `"Exibir grafo do resultado? (s/N)"`
- Modo CLI: flag `--grafico`

---

### 5. Animação passo a passo (`visualizer.py`)

Anima a busca frame a frame usando `matplotlib.animation`:

- **Painel esquerdo:** grafo da rede com nós e arestas acendendo progressivamente
- **Painel direito:** histórico em tempo real (últimas 12 linhas)
- Contador de passo e mensagens atualizado a cada frame

Código de cores na animação:

| Cor | Significado |
|---|---|
| Vermelho vivo | Nó/aresta ativo no frame atual |
| Azul | Origem |
| Verde | Encontrado |
| Laranja | Visitado |
| Vermelho escuro | Duplicata |
| Teal (verde-azul) | Mensagem de resposta |
| Cinza | Não visitado |

**Velocidades disponíveis:** lenta (1400ms), normal (900ms), rápida (400ms)

**Ativar:**
- Modo interativo: pergunta `"Exibir animacao passo a passo? (s/N)"` + escolha de velocidade
- Modo CLI: flag `--animar`

---

### 6. Estatísticas comparativas (`stats.py`)

Roda os 4 algoritmos para o mesmo cenário e compara os resultados.

**Tabela no terminal:**
```
==============================================================
  COMPARATIVO — no: n1  |  recurso: r9  |  TTL=10
==============================================================
+--------------------+------------+--------------+------------+
| Algoritmo          | Encontrado | Mensagens    | Nos Visit. |
+--------------------+------------+--------------+------------+
| Flooding           | SIM (n6)   | 11           | 6          |
| Inf. Flooding      | SIM (n6)   | 11           | 6          |
| Random Walk        | SIM (n6)   | 6            | 5          |
| Inf. R. Walk       | SIM (n6)   | 4            | 4          |
+--------------------+------------+--------------+------------+
  Menor numero de mensagens: Inf. R. Walk (4 msgs)
```

**Gráfico de barras:** barras cheias = mensagens, barras claras = nós visitados, valores em cima de cada barra, marca "NAO ENCONTRADO" quando TTL insuficiente.

**Ativar:**
- Modo interativo: escolha modo `2` no menu
- CLI: não há flag dedicada (usar modo interativo para comparativo)

---

## Como executar

**Dependências:**
```bash
pip install matplotlib networkx
```

**Modo interativo (recomendado para apresentação):**
```bash
python main.py
```

**Modo direto (testes rápidos):**
```bash
# Busca simples
python main.py examples/network_small.json n1 r9 --algo flooding --ttl 10

# Com histórico
python main.py examples/network_small.json n1 r9 --algo flooding --ttl 10 --historico

# Com grafo estático
python main.py examples/network_small.json n1 r9 --algo flooding --ttl 10 --grafico

# Com animação
python main.py examples/network_small.json n1 r9 --algo flooding --ttl 10 --animar

# Combinado
python main.py examples/network_large.json n1 r26 --algo random_walk --ttl 20 --historico --grafico --animar
```

---

## Checklist dos requisitos do enunciado

| Requisito | Status |
|---|---|
| Leitura de arquivo de configuração (JSON) | ✅ |
| Validação: rede conexa | ✅ |
| Validação: grau mín/máx de vizinhos | ✅ |
| Validação: nós sem recursos | ✅ |
| Validação: sem self-loops | ✅ |
| Algoritmo `flooding` | ✅ |
| Algoritmo `informed_flooding` | ✅ |
| Algoritmo `random_walk` | ✅ |
| Algoritmo `informed_random_walk` | ✅ |
| Contagem de mensagens trocadas | ✅ |
| Contagem de nós envolvidos | ✅ |
| Visualização gráfica da rede (opcional) | ✅ |
| Animação da busca em tempo real (opcional) | ✅ |
