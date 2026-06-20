# Garmin Connect Dashboard (Docker)

Dashboard web local que consome a biblioteca `python-garminconnect`
deste repositório e expõe gráficos e relatórios das principais
métricas do Garmin Connect.

## Stack

| Componente   | Função                                        |
|--------------|-----------------------------------------------|
| FastAPI      | Servidor HTTP + endpoints JSON                |
| Jinja2       | Templates HTML (server-rendered shell)        |
| Chart.js     | Gráficos no navegador (carregado via CDN)     |
| garminconnect| Cliente da API Garmin (versão deste repo)     |

A imagem é multi-stage usando `python:3.12-slim`, instala o
`garminconnect` direto do código fonte deste repositório (não do PyPI)
para herdar todas as correções aplicadas no fork.

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
