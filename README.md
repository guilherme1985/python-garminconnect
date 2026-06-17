[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor no GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

# Python: Garmin Connect

Biblioteca Python 3 para acesso à API do Garmin Connect, com dois exemplos prontos para uso:

- **`example.py`** — Exemplo básico de autenticação, armazenamento de tokens e chamadas à API
- **`demo.py`** — Demo completo com acesso a **130+ métodos da API** organizados em **13 categorias**

```bash
$ ./demo.py
🏃‍♂️ Full-blown Garmin Connect API Demo - Main Menu
==================================================
Selecione uma categoria:

  [1] 👤 Usuário & Perfil
  [2] 📊 Saúde & Atividade Diária
  [3] 🔬 Métricas Avançadas de Saúde
  [4] 📈 Histórico & Tendências
  [5] 🏃 Atividades & Treinos
  [6] ⚖️ Composição Corporal & Peso
  [7] 🏆 Metas & Conquistas
  [8] ⌚ Dispositivo & Técnico
  [9] 🎽 Equipamentos
  [0] 💧 Hidratação & Bem-Estar
  [a] 🔧 Sistema & Exportação
  [b] 📅 Planos de Treino
  [c] ⛳ Golfe

  [q] Sair

Faça sua seleção:
```

## Cobertura da API

- **Total de métodos**: 134+ endpoints únicos
- **Categorias**: 13 seções organizadas
- **Usuário & Perfil**: 4 métodos (informações básicas do usuário, configurações)
- **Saúde & Atividade Diária**: 9 métodos (dados de saúde do dia)
- **Métricas Avançadas**: 12 métodos (aptidão física, HRV, VO2, prontidão para treino, tolerância ao esforço)
- **Histórico & Tendências**: 9 métodos (consultas por período, agregados semanais)
- **Atividades & Treinos**: 38 métodos (gerenciamento completo de atividades, upload tipado, agendamento, importação, edição)
- **Composição Corporal & Peso**: 8 métodos (rastreamento de peso e composição)
- **Metas & Conquistas**: 15 métodos (desafios, badges, metas)
- **Dispositivo & Técnico**: 7 métodos (informações e configurações do dispositivo)
- **Equipamentos**: 7 métodos (gerenciamento de equipamentos)
- **Hidratação & Bem-Estar**: 12 métodos (hidratação, nutrição, pressão arterial, ciclo menstrual)
- **Sistema & Exportação**: 4 métodos (relatórios, logout, GraphQL)
- **Planos de Treino**: 3 métodos (planos, plano por ID, plano adaptativo por ID)
- **Golfe**: 3 métodos (resumo do placar, detalhe do placar, dados de cada tacada)

## 📖 Sobre

Esta biblioteca permite que desenvolvedores acessem programaticamente dados do Garmin Connect, incluindo:

- **Métricas de Saúde**: Frequência cardíaca, sono, estresse, composição corporal, SpO2, HRV
- **Dados de Atividade**: Treinos, upload tipado de treinos (corrida, ciclismo, natação, caminhada, trilha), agendamento, exercícios, status de treino, métricas de desempenho, importação direta (sem re-exportação do Strava)
- **Nutrição**: Diários alimentares diários, refeições e configurações nutricionais
- **Golfe**: Resumos de placares, detalhes, dados tacada a tacada
- **Informações de Dispositivo**: Dispositivos conectados, configurações, alarmes, dados solares
- **Metas & Conquistas**: Recordes pessoais, badges, desafios, previsões de corrida
- **Dados Históricos**: Tendências, acompanhamento de progresso, consultas por período

Compatível com todas as contas do Garmin Connect. Veja <https://connect.garmin.com/>

## 📦 Instalação

Instale via PyPI:

```bash
pip install --upgrade garminconnect curl_cffi
```

## Executar o demo (recomendado)

Clone o repositório e execute:

```bash
python3 -m venv .venv --copies
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -e ".[example]"

python3 ./example.py   # exemplo básico de introdução
python3 ./demo.py      # demo completo (130+ métodos da API)
```

## 🛠️ Desenvolvimento

Este projeto usa [PDM](https://pdm.fming.dev/) para gerenciamento de dependências e automação de tarefas.

> **⚠️ Importante**: Crie um ambiente virtual antes em instalações Python gerenciadas externamente (Debian/Ubuntu) para evitar conflitos com pacotes do sistema.

```bash
python3 -m venv .venv --copies
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install pdm
python -m pdm install --group :all
pre-commit install --install-hooks  # opcional, mas recomendado
```

> **Nota**: Usar `python -m pdm` em vez de `pdm` evita problemas de PATH em algumas configurações Windows onde `pip install pdm` instala o executável fora dos diretórios do PATH. Após `pdm install`, os comandos `pdm run ...` funcionam normalmente com o venv ativo.

**Comandos de desenvolvimento:**

```bash
pdm run format      # Formata o código automaticamente (isort, black, ruff --fix)
pdm run lint        # Verifica qualidade do código (isort, ruff, black, mypy)
pdm run codespell   # Verifica ortografia
pdm run test        # Executa a suíte de testes
pdm run testcov     # Executa os testes com relatório de cobertura
pdm run all         # Executa todas as verificações (lint + codespell + pre-commit + test)
pdm run clean       # Limpa artefatos de build e cache
pdm run build       # Empacota para distribuição
pdm run publish     # Empacota e publica no PyPI
pdm run --list      # Lista todos os comandos disponíveis
```

Execute `pdm run format && pdm run lint && pdm run test` antes de enviar PRs.

## 🔐 Autenticação

A autenticação usa o mesmo fluxo SSO móvel do aplicativo oficial Garmin Connect para Android.
Nenhum navegador é necessário.

**Como funciona:**

1. **Primeiro login**: Autentica via `sso.garmin.com/mobile/api/login` usando o client ID do app Android. Se MFA for necessário, um callback (`prompt_mfa`) solicita o código de uso único.
2. **Troca de token**: O ticket de serviço é trocado por tokens DI OAuth Bearer (`access_token` + `refresh_token`) via `diauth.garmin.com`. Os tokens são armazenados em `~/.garminconnect/garmin_tokens.json`.
3. **Renovação automática**: Antes de cada requisição à API, a biblioteca verifica se o token DI está prestes a expirar e o renova automaticamente — sem interação do usuário.

**Tempo de vida da sessão:**
- Os tokens DI se renovam indefinidamente enquanto o refresh token permanecer válido.
- Um novo login completo com credenciais (e possivelmente MFA) só é necessário se o refresh token expirar ou for revogado.

**Armazenamento de tokens:**
```bash
~/.garminconnect/garmin_tokens.json   # salvo automaticamente, permissão 0600
```

**Login resiliente (multi-estratégia + validação de token):**

O método `login()` tenta várias estratégias de autenticação em ordem (mobile, widget SSO, portal web — cada uma com e sem impressão digital TLS) e só declara sucesso quando o token resultante é efetivamente aceito pela API. Se uma estratégia obtiver um token que a API rejeitar posteriormente (condição específica de região/conta — veja [#369](https://github.com/cyberjunky/python-garminconnect/issues/369)), a biblioteca automaticamente tenta a próxima estratégia. Defina `Garmin(..., verify_login=False)` para restaurar o comportamento legado de "primeiro token vence".

**Token em cache inválido e auto-recuperação:** quando um `tokenstore` é fornecido, `login()` carrega esses tokens antes da cadeia de estratégias e encerra se eles carregarem — então tokens em cache inválidos costumavam falhar em toda execução. A biblioteca agora detecta isso: se tokens em cache forem rejeitados pela API, ela os descarta e realiza um login completo com credenciais automaticamente. Para forçar um estado limpo você mesmo (ex.: entre uma tentativa com falha e uma nova tentativa), chame:

```python
g.logout()            # limpa a autenticação em memória + tokens em cache (usa GARMINTOKENS)
g.logout(tokenstore)  # ou passe um caminho explícito
```

## 🧪 Testes

Execute `example.py` uma vez primeiro para criar os tokens salvos em `~/.garminconnect`, depois:

```bash
pdm run test        # Executa todos os testes
pdm run testcov     # Executa os testes com relatório de cobertura
```

Opcional: isolar os tokens de teste

```bash
export GARMINTOKENS="$(mktemp -d)"
python3 ./example.py   # cria um arquivo de token novo para os testes
pdm run test
```

**Nota:** Os testes usam cassetes VCR para gravar/reproduzir respostas da API. Se os testes falharem com erros de autenticação, certifique-se de que tokens válidos existem em `~/.garminconnect` (execute `example.py` primeiro).

## 📦 Publicação

Para mantenedores do pacote:

**Configurar credenciais do PyPI:**

```bash
pip install twine
```

```ini
[pypi]
username = __token__
password = <TOKEN_API_PYPI>
```

Recomendado: use variáveis de ambiente e restrinja as permissões do arquivo

```bash
chmod 600 ~/.pypirc
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="<TOKEN_API_PYPI>"
```

**Publicar nova versão:**

```bash
pdm run publish    # Empacota e publica no PyPI
```

**Passos alternativos de publicação:**

```bash
pdm run build      # Somente empacota
pdm publish        # Publica pacote já compilado
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja como você pode ajudar:

- **Reportar Problemas**: Bugs e solicitações de funcionalidades via issues no GitHub
- **Enviar PRs**: Melhorias de código, novas funcionalidades, atualizações de documentação
- **Testes**: Ajude a testar novas funcionalidades e reporte problemas de compatibilidade
- **Documentação**: Melhore exemplos, adicione casos de uso, corrija erros

**Antes de contribuir:**
1. Configure seu ambiente de desenvolvimento (veja [Desenvolvimento](#️-desenvolvimento) acima)
2. Formate e verifique: `pdm run format && pdm run lint`
3. Execute os testes: `pdm run test`
4. Siga o estilo e padrões de código existentes

### Jupyter Notebook

Explore a API interativamente com o [notebook de referência](https://github.com/cyberjunky/python-garminconnect/blob/master/docs/reference.ipynb).

### Exemplos de Código Python

```python
import os
from datetime import date
from garminconnect import Garmin

# Primeira execução: faz login e salva tokens em ~/.garminconnect
# Execuções seguintes: carrega tokens salvos e os renova automaticamente
client = Garmin(
    os.getenv("EMAIL"),
    os.getenv("PASSWORD"),
    prompt_mfa=lambda: input("Código MFA: "),
)
client.login("~/.garminconnect")

# Obter estatísticas do dia
hoje = date.today().isoformat()
stats = client.get_stats(hoje)

# Obter dados de frequência cardíaca
hr_data = client.get_heart_rates(hoje)
print(f"FC em repouso: {hr_data.get('restingHeartRate', 'n/d')}")
```

### Treinos Tipados (Modelos Pydantic)

A biblioteca inclui modelos de treino tipados opcionais para criar definições de treino com segurança de tipo:

```bash
pip install garminconnect[workout]
```

```python
from garminconnect.workout import (
    RunningWorkout, WorkoutSegment,
    create_warmup_step, create_interval_step, create_cooldown_step,
    create_repeat_group,
)

# Criar um treino de corrida estruturado
workout = RunningWorkout(
    workoutName="Corrida Leve",
    estimatedDurationInSecs=1800,
    workoutSegments=[
        WorkoutSegment(
            segmentOrder=1,
            sportType={"sportTypeId": 1, "sportTypeKey": "running"},
            workoutSteps=[create_warmup_step(300.0)]
        )
    ]
)

# Fazer upload e, opcionalmente, agendar
result = client.upload_running_workout(workout)
client.schedule_workout(result["workoutId"], "2026-03-20")

# Deletar um treino ou removê-lo do calendário
client.delete_workout(workout_id)
client.unschedule_workout(scheduled_workout_id)
```

**Classes de treino disponíveis:** `RunningWorkout`, `CyclingWorkout`, `SwimmingWorkout`, `WalkingWorkout`, `HikingWorkout`, `MultiSportWorkout`, `FitnessEquipmentWorkout`

**Funções auxiliares:** `create_warmup_step`, `create_interval_step`, `create_recovery_step`, `create_cooldown_step`, `create_repeat_group`

### Dependências Opcionais

| Extra | O que habilita |
|-------|---------------|
| `garminconnect[workout]` | Modelos Pydantic de `workout.py` para upload de treinos tipados |
| `garminconnect[typed]` | Objetos de resposta validados por Pydantic via `g.typed.*` (experimental) |
| `garminconnect[example]` | `readchar` para os scripts interativos `demo.py` / `example.py` |

### Recursos Adicionais

- **Exemplo simples**: [example.py](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/example.py) — Guia de introdução
- **Demo completo**: [demo.py](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/demo.py) — Todos os 130+ métodos da API
- **Casos de teste**: Exemplos de uso do mundo real em `tests/`

## 🙏 Agradecimentos

Agradecimentos especiais a todos os colaboradores que ajudaram a melhorar este projeto:

- **Contribuidores da comunidade**: Relatórios de bugs, solicitações de funcionalidades e melhorias de código
- **Relatores de problemas**: Ajudando a identificar e resolver problemas de compatibilidade
- **Desenvolvedores de funcionalidades**: Adicionando novos endpoints e funcionalidades à API
- **Autores de documentação**: Melhorando exemplos e guias de uso

Este projeto cresce graças ao envolvimento e feedback da comunidade.

## 💖 Apoie Este Projeto

Se esta biblioteca é útil para seus projetos, considere apoiar seu desenvolvimento e manutenção continuados:

### 🌟 Como Apoiar

- **⭐ Marque este repositório com estrela** — Ajude outros a descobrir o projeto
- **💰 Apoio financeiro** — Contribua para os custos de desenvolvimento e hospedagem
- **🐛 Reporte problemas** — Ajude a melhorar a estabilidade e compatibilidade
- **📖 Divulgue** — Compartilhe com outros desenvolvedores

### 💳 Opções de Apoio Financeiro

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor no GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

**Por que apoiar?**
- Mantém o projeto ativamente desenvolvido
- Permite correções de bugs e novas funcionalidades mais rápidas
- Apoia custos de infraestrutura (testes, IA, CI/CD)
- Reconhece centenas de horas de desenvolvimento

Toda contribuição, independentemente do tamanho, faz diferença e é muito apreciada! 🙏

[releases-shield]: https://img.shields.io/github/release/cyberjunky/python-garminconnect.svg?style=for-the-badge
[releases]: https://github.com/cyberjunky/python-garminconnect/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/cyberjunky/python-garminconnect.svg?style=for-the-badge
[commits]: https://github.com/cyberjunky/python-garminconnect/commits/main
[license-shield]: https://img.shields.io/github/license/cyberjunky/python-garminconnect.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-cyberjunky-blue.svg?style=for-the-badge
