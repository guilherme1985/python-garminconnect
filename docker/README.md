# Garmin Connect Dashboard (Docker)

Dashboard web local que consome a biblioteca `python-garminconnect`
deste repositório e expõe gráficos e relatórios das principais
métricas do Garmin Connect.

## Stack

| Componente   | Função                                                     |
|--------------|------------------------------------------------------------|
| FastAPI      | Servidor HTTP + endpoints JSON, scheduler do coletor       |
| Jinja2       | Templates HTML (server-rendered shell)                     |
| Chart.js     | Gráficos no navegador (carregado via CDN)                  |
| garminconnect| Cliente da API Garmin (versão deste repo) + DiskCache F5-02|
| InfluxDB 2.7 | Séries temporais persistidas pelo coletor (F6-02)          |
| Grafana 10.4 | Dashboards pré-configurados via provisioning (F6-04)       |

A imagem da app é multi-stage usando `python:3.12-slim`, instala o
`garminconnect` direto do código fonte deste repositório (não do PyPI)
para herdar todas as correções aplicadas no fork.

### Topologia

```
 ┌──────────┐    ┌──────────────┐    ┌──────────┐
 │ Garmin   │◄───┤ dashboard    │───►│ InfluxDB │
 │ Connect  │    │ (FastAPI +   │    │ (séries) │
 └──────────┘    │  scheduler)  │    └────┬─────┘
                 └──────┬───────┘         │
                        │                 ▼
                        ▼            ┌────────┐
                 http://:8000        │Grafana │
                                     │ :3000  │
                                     └────────┘
```

O `scheduler.py` roda como tarefa asyncio dentro do dashboard (`lifespan`)
e a cada `COLLECT_INTERVAL_S` (default 900s = 15min) busca os últimos 7
dias e grava no InfluxDB via line protocol HTTP — sem dependências
extras (stdlib `urllib`). DiskCache em `/data/cache` reduz hits na API
Garmin.

## Pré-requisitos

1. Conta Garmin Connect com credenciais válidas
2. Docker + docker compose v2
3. Tokens de autenticação já gerados localmente — o container **não
   suporta MFA interativo**. Gere os tokens 1 vez pelo `example.py`
   na raiz do repo, depois copie/monte o diretório.

## Setup rápido

```bash
cd docker/

# 1. Configure credenciais
cp .env.example .env
$EDITOR .env   # preencha GARMIN_EMAIL e GARMIN_PASSWORD

# 2. Gere os tokens uma vez (na raiz do repo, fora do container)
cd .. && python3 example.py   # responde MFA se necessário
cp -r ~/.garminconnect docker/tokens
cd docker/

# 3. Suba o stack
docker compose up -d --build

# 4. Acesse
open http://localhost:8000
```

## Acesso após `docker compose up`

| Serviço    | URL                  | Credenciais             |
|------------|----------------------|-------------------------|
| Dashboard  | http://localhost:8000 | (sessão Garmin)         |
| InfluxDB   | http://localhost:8086 | admin / changeme123 ¹   |
| Grafana    | http://localhost:3000 | admin / admin ¹         |

¹ valores default do `.env.example` — **troque em produção**.

Em Grafana, o dashboard "Garmin · Saúde Diária" aparece em
`Dashboards → Garmin` automaticamente (provisioning). Dados começam a
aparecer após o primeiro tick do coletor (até 15 min).

## Páginas disponíveis

| Rota          | Conteúdo                                       |
|---------------|------------------------------------------------|
| `/`           | Cards-resumo de ontem (passos, calorias, etc.) |
| `/steps`      | Gráfico de barras + meta nos últimos 30 dias   |
| `/heart`      | Linha de frequência cardíaca intra-dia (ontem) |
| `/sleep`      | Barras empilhadas de estágios (14 dias)        |
| `/stress`     | Estresse médio/máx nos últimos 7 dias          |
| `/battery`    | Body Battery carregado vs drenado (7 dias)     |
| `/activities` | Distribuição por tipo + tabela das últimas 50  |
| `/weight`     | Linha de peso (90 dias) + IMC                  |
| `/hrv`        | HRV intra-dia + summary                        |
| `/training`   | Training Readiness (score, sono, recuperação)  |
| `/healthz`    | Healthcheck JSON simples                       |

Cada página tem versão JSON em `/api/<nome>` — útil para integrar
com outros sistemas (Grafana, n8n, scripts).

## Estrutura

```
docker/
├── Dockerfile              # imagem da aplicação
├── docker-compose.yml      # serviço único (dashboard)
├── .env.example            # template de credenciais
├── .dockerignore           # exclui logs/, venv, .git, etc.
├── tokens/                 # ← criado pelo usuário (volume)
└── app/
    ├── main.py             # rotas FastAPI
    ├── garmin_service.py   # singleton + cache do cliente
    ├── requirements.txt
    ├── static/styles.css
    └── templates/
        ├── base.html
        ├── dashboard.html
        ├── chart_page.html # template genérico (steps/heart/sleep/...)
        ├── activities.html
        └── error.html
```

## Variáveis de ambiente

Reaproveita as mesmas do projeto-raiz:

- `GARMIN_EMAIL` / `GARMIN_PASSWORD` — credenciais (obrigatório)
- `GARMIN_IS_CN` — `true` para Garmin China
- `GARMIN_LOGIN_TIMEOUT` — timeout da cadeia de login (default 180s)
- `GARMINTOKENS` — caminho do tokenstore (padrão `/data/tokens`)
- `DASHBOARD_PORT` — porta exposta no host (default 8000)

## Logs e debug

```bash
docker compose logs -f dashboard
```

Erros de login aparecem na sidebar como banner vermelho; erros 5xx
caem em `/error` template com detalhes.

## Limitações conhecidas

- **MFA**: não há fluxo interativo no container — gere tokens fora dele.
- **Cache**: o dashboard sempre busca dados frescos da API. Sob carga
  pesada, considere adicionar Redis (roadmap F6-02).
- **Cobertura**: 10 páginas / ~12 endpoints. A biblioteca tem 130+
  métodos — adicione novas páginas em `main.py` reusando
  `chart_page.html` para gráficos genéricos.

## Próximos passos (no roadmap)

- F6-02 Redis cache de respostas
- F6-03 Stack completa com Postgres + Grafana
- F6-04 Endpoints para exportação CSV/InfluxDB
