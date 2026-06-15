# Resumo e Contexto do Trabalho 7 (Hand-off para IAs)

Este documento foi gerado para servir como **contexto central** caso você (usuário) precise continuar o trabalho usando outra IA, ou caso inicie uma nova sessão no futuro. Ele resume o que é o projeto, as decisões tomadas e como a arquitetura está estruturada.

## 1. O Contexto Acadêmico
- **Disciplina:** Computação Distribuída
- **Professor:** Nabor C. Mendonça
- **Atividade:** Trabalho 7 – Implementação de Algoritmos de Busca em Sistemas P2P
- **Histórico:** Os trabalhos anteriores (Trabalho 2 e 3) focaram em infraestrutura pesada usando Docker Compose, Nginx, WordPress e Locust (testes de carga). O usuário solicitou que este trabalho 7 também rodasse via Docker Compose para manter o padrão de entrega, embora o código seja puramente em Python.

## 2. O que o Trabalho Exigia (Requisitos)
O PDF do trabalho exigia a construção do núcleo (backend) de um simulador P2P semântico simples:
1. **Representação da Rede:** Ler a estrutura de um arquivo texto (adaptamos para JSON) mapeando os Nós, suas Arestas e seus Recursos.
2. **Regras de Validação:** A rede **não** pode carregar se falhar em 5 regras: 
   - A contagem de nós deve bater.
   - Não pode haver arestas de loop (nó apontando para si mesmo).
   - Todo nó deve ter pelo menos um recurso.
   - O grau de conexões do nó deve estar dentro dos limites min/max.
   - A rede não pode ser particionada (tem que ser 100% conexa).
3. **Algoritmos de Busca:** Implementar 4 algoritmos:
   - `flooding`: Inundação em largura.
   - `informed_flooding`: Inundação consultando o cache local primeiro.
   - `random_walk`: Passeio aleatório passando a mensagem para apenas 1 vizinho por vez.
   - `informed_random_walk`: Passeio aleatório consultando o cache local.
4. **Métricas:** Para cada busca, o programa deve cuspir se o recurso foi achado, onde, quantas mensagens foram enviadas na rede e quantos nós foram visitados.

## 3. Arquitetura Atual e Decisões de Design
- **Linguagem:** Python 3.10 puro (Standard Library). **Proibido o uso de dependências externas** (sem pandas, sem flask, sem fastapi).
- **Interface:** O projeto é uma **CLI (Interface de Linha de Comando)** interativa. 
  - *Nota Histórica:* Inicialmente, o projeto foi concebido com uma interface web rebuscada (HTML, CSS Glassmorphism, SVG/D3.js). O usuário pediu para deletar o frontend web inteiro e deixar apenas um script seco no terminal, pois o objetivo é apenas mostrar o funcionamento bruto ao professor sem distrações.
- **Docker:** O aplicativo foi envelopado em um `Dockerfile` leve e roda via `docker-compose run simulador` em modo interativo (`stdin_open: true` e `tty: true`).

## 4. Estrutura do Código
- `main.py`: O entry point. É um script que fica em loop fazendo perguntas no terminal (caminho do arquivo, qual nó buscar, etc).
- `simulator/network.py`: Contém a classe `P2PNetwork`. É aqui que fica o parser do JSON e as lógicas restritas das 5 regras de validação.
- `simulator/algorithms.py`: Contém a lógica pura (os algoritmos de grafos BFS e Random Walk) que iteram pela rede contabilizando o número de saltos, nós e cache.
- `examples/`: Uma pasta com vários `.json` de redes já desenhadas. Algumas são válidas (ex: `network_medium.json`) e outras foram feitas propositalmente inválidas (ex: `network_invalid_loop.json`) para testar se as validações da `network.py` estão funcionando.

## 5. Próximos Passos (se houver)
O código está **100% finalizado de acordo com o escopo**. Caso uma IA futura assuma este repositório, ela **não deve** tentar recriar um servidor web ou uma interface gráfica, a menos que o usuário explicitamente revogue sua decisão anterior de manter o projeto puramente em CLI. Alterações futuras devem se concentrar em possíveis bugs nos algoritmos de travessia do grafo (`algorithms.py`).
