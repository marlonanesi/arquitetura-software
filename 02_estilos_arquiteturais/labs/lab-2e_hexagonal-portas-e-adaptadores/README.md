# Lab 2E: Arquitetura hexagonal: trocando o adaptador sem tocar no domínio

Aula prática da seção 2 (Estilos Arquiteturais), depois da aula 2.13.

| | |
|---|---|
| Aulas relacionadas | 2.13 (arquitetura hexagonal: separando domínio de infraestrutura) |
| Ambiente | Código local (Python), com Docker opcional |
| Ordem de estudo | Trilha Hexagonal, passo 1 de 2 (o lab 2F evolui este domínio para CQRS e Event Sourcing) |

## Objetivo

Na aula 2.13 vimos o caso da LunaLog que trocou o provedor de mapas: o código chamava a API do Google em 23 pontos, e a troca levou seis semanas e três bugs de regressão. Com portas e adaptadores, seria uma implementação nova por trás de uma interface que já existe. Neste lab você vê isso funcionando: um **núcleo de domínio** (a confirmação de entrega) que define **portas** e é cercado por **adaptadores** trocáveis (banco, notificação, provedor de mapas), e as consequências práticas, em testes e em mudanças.

## O que você vai ver

- Um **domínio sem nenhum import de framework ou de driver**, só regras de negócio
- **Testes do domínio em milissegundos**, com adaptadores em memória, sem banco nem rede
- **Troca do repositório** (memória, SQLite, PostgreSQL) por variável de ambiente, sem alterar o domínio
- **Troca do canal de notificação** (log, webhook) e do **provedor de mapas** (Google, HERE), e a prova de que o domínio não mudou
- **Adicionar um adaptador novo**: um arquivo novo e duas linhas na fábrica
- Um **teste de arquitetura** que quebra o build quando alguém faz o domínio importar infraestrutura

## Arquitetura do lab

```mermaid
flowchart LR
    CLI["CLI<br/>(adaptador de entrada)"] --> UC
    subgraph H["Hexágono (domínio)"]
        UC["casos de uso<br/>ConfirmarEntrega"] --> E["Entrega<br/>(regras de negócio)"]
        UC --- P(("portas"))
    end
    P -.-> R["Repositório<br/>memória · SQLite · PostgreSQL"]
    P -.-> N["Notificador<br/>log · webhook"]
    P -.-> G["Geocodificador<br/>Google · HERE"]
    F["fabrica.py<br/>(raiz de composição)"] -. escolhe por variável .-> R
    F -.-> N
    F -.-> G
```

- O **domínio** (`src/confirmacao/dominio/`) tem as regras (`entrega.py`), os casos de uso e as **portas** (`portas.py`), que são contratos descritos como interfaces.
- Os **adaptadores** (`src/confirmacao/adaptadores/`) implementam as portas para cada tecnologia. A dependência aponta **para dentro**: os adaptadores conhecem o domínio, o domínio não conhece os adaptadores.
- A **fábrica** (`fabrica.py`) é o único lugar que conhece os dois lados. Ela escolhe os adaptadores pelas variáveis de ambiente.
- A regra de negócio do lab: *só se confirma uma entrega que está em rota, a até 100 m do endereço*.

## Pré-requisitos

- Python 3.12 ou superior e git
- Para rodar sem instalar nada: Docker (opcional)
- O PostgreSQL (cenário 2) e o receptor de webhook (cenário 3) só aparecem via Docker Compose. O receptor publica a porta 9000, só em `127.0.0.1`, então ela precisa estar livre

Escolha uma das formas de executar:

**Local (sem Docker):**

```bash
pip install pytest
export PYTHONPATH=src            # no PowerShell: $env:PYTHONPATH = "src"
python -m confirmacao.cli demo
python -m pytest -q
```

**Com Docker (nada a instalar):**

```bash
docker compose build lab
docker compose --profile ferramentas run --rm lab                          # roda a demonstração
docker compose --profile ferramentas run --rm lab python -m pytest -q       # roda os testes
```

Os comandos abaixo usam o formato local; com Docker, troque o início por `docker compose --profile ferramentas run --rm [-e VAR=valor] lab`.

## Como executar

### Cenário 1: o domínio, sem infraestrutura

Leia na ordem: `dominio/entrega.py` (a regra), `dominio/portas.py` (o que o domínio precisa do mundo) e `dominio/casos_de_uso.py` (a orquestração). Nenhum deles importa banco, HTTP ou framework: só `dataclasses`, `datetime`, `enum`, `math`, `typing`.

```bash
python -m confirmacao.cli demo
```

O que observar: registra a entrega, inicia a rota, tenta confirmar a 2 km do endereço e a regra de negócio **recusa** (`motorista a 2046 m do destino (maximo 100 m)`), e então confirma no endereço e notifica. Roda com tudo em memória: nenhum banco, nenhuma rede.

Agora os testes do domínio:

```bash
python -m pytest -q tests/test_dominio.py tests/test_arquitetura.py
```

O que observar: `6 passed` em cerca de **0,1 segundo**. Os testes do domínio usam dublês escritos à mão em `tests/doubles.py` (um relógio fixo, um geocodificador fixo, um notificador que só guarda o que recebeu). Sem banco para subir, sem rede para falhar, sem esperas. É isso que permite ter dezenas de testes de regra de negócio e rodá-los a cada gravação do arquivo.

### Cenário 2: trocar o repositório sem tocar no domínio

Até aqui o repositório é em memória (os dados somem ao fim do processo). Troque para SQLite com **uma variável**:

```bash
export REPOSITORIO=sqlite SQLITE_PATH=/tmp/entregas.db
python -m confirmacao.cli criar E-200 "Av. Paulista, 1000"
python -m confirmacao.cli iniciar E-200
python -m confirmacao.cli confirmar E-200 -23.5632 -46.6544
python -m confirmacao.cli mostrar E-200
```

Cada comando é um processo diferente, e a entrega **persiste** entre eles. O domínio é o mesmo, o adaptador é outro.

Para o PostgreSQL, suba o banco (`docker compose up -d postgres`) e use `REPOSITORIO=postgres POSTGRES_URL=postgresql://luna:luna@localhost:5432/entregas` (adicione `ports: ["5432:5432"]` ao serviço ou rode pelo contêiner `lab`, que já traz a URL). O resultado é o mesmo.

Um valor inválido dá uma mensagem útil: `REPOSITORIO=mongo` responde `invalido. Opcoes: memoria, postgres, sqlite`.

Como saber que um adaptador novo é "equivalente" aos outros? O **teste de contrato** (`tests/test_contrato_repositorios.py`) roda a mesma bateria contra cada repositório:

```bash
docker compose --profile ferramentas run --rm lab python -m pytest -q tests
```

O que observar: `18 passed`, com os testes do repositório executados contra memória, SQLite e PostgreSQL. Um adaptador novo só precisa passar na mesma bateria.

### Cenário 3: trocar o canal de notificação

```bash
docker compose up -d receptor
NOTIFICADOR=webhook WEBHOOK_URL=http://localhost:9000/ python -m confirmacao.cli demo
docker compose logs receptor
```

(Pelo contêiner `lab`, o endereço do receptor já vem configurado.) Em vez de escrever uma linha no log, a notificação agora vira um POST HTTP, e o receptor imprime `WEBHOOK RECEBIDO: {"evento": "EntregaConfirmada", ...}`. O caso de uso `ConfirmarEntrega` não foi alterado: ele chama `notificador.entrega_confirmada(entrega)` e não sabe o que há do outro lado.

### Cenário 4: trocar o provedor de mapas

É a história da aula. Os dois adaptadores de geocodificação (`geocodificador_google.py` e `geocodificador_here.py`) recebem respostas em **formatos diferentes**, e cada um as traduz para a mesma `Coordenada` do domínio:

```bash
GEOCODIFICADOR=here python -m confirmacao.cli demo
```

Compare os dois arquivos. O formato do Google (`results[0].geometry.location.lat/lng`) e o da HERE (`items[0].position.lat/lng`) ficam **presos dentro do adaptador**. O domínio nunca vê a resposta do provedor. Se a LunaLog tivesse 23 chamadas diretas à API do Google, a troca seria 23 mudanças; aqui é uma variável.

(Os provedores são **simulados**, sem rede, para o lab rodar offline. O ponto é a fronteira, não a API real.)

### Cenário 5: adicionar um adaptador novo, e provar que o domínio não mudou

Registre a "impressão digital" do domínio:

```bash
bash scripts/checksum-dominio.sh
```

Saída de exemplo: `dominio: ed7afc2a9347001f  (5 arquivos)`. Agora o exercício: adicionar um **terceiro** provedor de mapas. O adaptador pronto está em `extras/`:

```bash
cp extras/geocodificador_osm.py src/confirmacao/adaptadores/
```

E registre-o na fábrica (`src/confirmacao/fabrica.py`), com **duas linhas**:

```python
from confirmacao.adaptadores.geocodificador_osm import GeocodificadorOsm      # junto dos outros imports
    "osm": lambda env: GeocodificadorOsm(),                                   # dentro de GEOCODIFICADORES
```

```bash
GEOCODIFICADOR=osm python -m confirmacao.cli demo
bash scripts/checksum-dominio.sh
```

O que observar: o provedor novo funciona, e a **impressão digital do domínio é exatamente a mesma**. Um adaptador novo custou **um arquivo novo e duas linhas na fábrica**, e **zero linhas** no domínio nem nos casos de uso. Para desfazer: apague o arquivo copiado e as duas linhas.

### Cenário 6: o teste de arquitetura barra a violação

A regra de dependência (o domínio não importa infraestrutura) é fácil de combinar e fácil de violar no calor de um prazo. O teste `tests/test_arquitetura.py` a verifica lendo os imports de cada arquivo do domínio. Quebre de propósito: adicione, na primeira linha de `src/confirmacao/dominio/entrega.py`:

```python
import sqlite3
```

```bash
python -m pytest -q tests/test_arquitetura.py
```

O que observar: o teste **falha** com a mensagem `entrega.py importa 'sqlite3'`. O "atalho" (já que preciso salvar, importo o driver aqui) é barrado pelo build, antes de virar hábito. Remova a linha e o teste volta a passar.

## Resultados de referência

| Verificação | Resultado |
|---|---|
| Testes do domínio e da arquitetura | 6 passam em cerca de 0,1 s |
| Todos os testes (inclui contrato dos 3 repositórios) | 18 passam em cerca de 0,4 s |
| Trocar memória por SQLite ou PostgreSQL | uma variável (`REPOSITORIO`), domínio inalterado |
| Trocar log por webhook | uma variável (`NOTIFICADOR`), domínio inalterado |
| Trocar Google por HERE | uma variável (`GEOCODIFICADOR`), domínio inalterado |
| Adicionar um terceiro provedor | 1 arquivo novo e 2 linhas na fábrica; impressão digital do domínio idêntica |
| `import sqlite3` no domínio | `test_arquitetura` falha apontando o arquivo |

## Como limpar

```bash
docker compose down -v
```

Se usou o SQLite local, apague o arquivo (`entregas.db` ou o caminho de `SQLITE_PATH`).

## Estrutura da pasta

```
lab-2e_hexagonal-portas-e-adaptadores/
  README.md
  src/confirmacao/
    dominio/                  (entrega.py, geo.py, portas.py, casos_de_uso.py)
    adaptadores/              (repositórios, notificadores, geocodificadores, relógio)
    fabrica.py                (raiz de composição)
    cli.py                    (adaptador de entrada)
  tests/
    test_dominio.py           (regras, com dublês em memória)
    test_contrato_repositorios.py   (a mesma bateria para cada repositório)
    test_arquitetura.py       (regra de dependência)
    doubles.py
  extras/geocodificador_osm.py    (para o exercício do cenário 5)
  receptor/receptor.py        (receptor de webhook de brincadeira)
  scripts/checksum-dominio.sh
  docker-compose.yml, Dockerfile, pytest.ini
```

## Limites deste lab

- O domínio é pequeno de propósito. Em sistemas reais, o domínio tem agregados, eventos e mais regras, e o custo de manter portas e adaptadores é maior. A arquitetura hexagonal compensa quando há **regras de negócio relevantes** e **infraestrutura que muda**; em um CRUD simples, é cerimônia.
- Os provedores de mapas são simulados. Em produção, o adaptador também cuidaria de autenticação, timeouts, limites de taxa e tratamento de erros do provedor, e traduziria os erros dele para erros do domínio.
- O repositório devolve a entidade inteira e não trata concorrência (duas confirmações simultâneas). Em produção, um controle otimista de versão ou uma transação adequada seria necessário.
- Há um único adaptador de entrada (a CLI). Uma API HTTP ou um consumidor de fila seriam outros adaptadores de entrada chamando os mesmos casos de uso.
- O teste de arquitetura é caseiro (lê os imports com `ast`) para o lab ser autocontido. Em projetos maiores, use uma ferramenta (por exemplo, import-linter em Python, como no lab 2A).
- Este domínio é reaproveitado no lab 2F, que o evolui para CQRS e Event Sourcing.

## Para pensar

1. O domínio define as portas, e os adaptadores se adaptam a elas. O que muda na forma de dividir o trabalho entre times se você pensar assim, de dentro para fora?
2. Quantas "chamadas diretas" a serviços externos (mapas, pagamento, e-mail) existem hoje no seu sistema? Quanto custaria trocar uma delas?
3. Os testes do domínio rodam em 0,1 s. O que isso muda na frequência com que você os roda e na confiança ao refatorar?
4. Onde termina a regra de negócio e começa a infraestrutura? (Dica: a confirmação por distância é regra de negócio; o formato da resposta do provedor de mapas não é.)
