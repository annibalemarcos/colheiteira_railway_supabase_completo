# 🚀 Colheiteira - Análise Web Completa

Sistema avançado de análise de qualidade de websites com múltiplos critérios e comparação com concorrentes.

## 📋 Funcionalidades

### ✅ Análises Implementadas

1. **Ortografia** - Detecta erros de português e problemas gramaticais
2. **Links** - Identifica links quebrados (404) e lentos
3. **Imagens** - Analisa qualidade, tamanho, otimização e alt text
4. **Redes Sociais** - Avalia presença e qualidade dos perfis sociais
5. **Lighthouse** - Performance, acessibilidade e boas práticas
6. **SEO** - Otimização para motores de busca

### 🎯 Diferenciais

- ✨ Dashboard interativo com gráficos em Bootstrap 5
- 🧺 Modo bulk com toggle para analisar vários sites em sequência
- ⏱️ Pausas aleatórias configuráveis entre sites para reduzir rajadas de requisições
- ⚙️ Menu lateral e painel de configurações no próprio dashboard
- 📊 Comparação automática com 3 concorrentes de referência
- 🎨 Visualização clara dos problemas e soluções
- 🏆 Sistema de ranking (A, B, C, D, E)
- 💡 Sugestões práticas de melhorias

## 🔧 Instalação

### Pré-requisitos

```bash
# Python 3.10+
python --version

# Node.js (para Lighthouse)
node --version
npm install -g lighthouse
```

### Dependências Python

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Instalar LanguageTool (Ortografia)

```bash
# O LanguageTool será baixado automaticamente na primeira execução
# Requer Java instalado
java -version
```

## 🚀 Uso

### 1. Executar Análise

```bash
python main.py https://seusite.com
```

Isso irá:
- Executar todos os plugins
- Gerar score para cada categoria
- Calcular score final ponderado
- Salvar resultados em `output/data.json`

### 2. Visualizar Dashboard

```bash
python server/app.py
```

Acesse: http://localhost:5840

Login padrão:

```text
Usuário: admin
Senha: 000000
```

Não existe cadastro. Todas as telas e APIs do painel exigem sessão autenticada; apenas `/login` e `/health` ficam públicos.

## 🌾 Dashboard Flask na porta 5840

O app agora inclui um dashboard Flask renovado, com tela para disparar análises, logs em tempo real, histórico de resultados, gráficos por plugin e exportação do JSON.

```bash
python server/app.py
# ou, no Windows:
run_dashboard.bat
```

Acesse: http://localhost:5840

Rotas úteis:

- `GET/POST /login` — autenticação do administrador
- `GET /logout` — encerra a sessão
- `GET /` — dashboard visual
- `POST /api/analyze` — inicia uma análise enviando `{ "url": "https://site.com" }`
- `POST /api/bulk_analyze` — inicia análise em lote enviando `{ "urls": ["https://a.com", "https://b.com"], "settings": {"min_delay": 8, "max_delay": 25, "max_urls": 30} }`
- `GET /api/jobs/<job_id>` — status/logs de uma análise
- `GET /api/data` — última análise salva
- `GET /api/history` — histórico de análises
- `GET /api/settings` — configurações padrão do dashboard
- `GET /api/export/latest` — baixa o último JSON

### Segurança do login

Por padrão, o painel usa `admin` / `000000`, conforme solicitado. Para publicar na internet, mantenha esses valores ou substitua-os por variáveis de ambiente sem editar o código:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=000000
SECRET_KEY=uma-chave-longa-e-aleatoria
```

A sessão dura 12 horas, utiliza cookie `HttpOnly` e `SameSite=Lax`. No Railway, o cookie seguro HTTPS é ativado automaticamente. O endpoint `/health` permanece público para o healthcheck da plataforma.

### Modo bulk

No dashboard, ative o toggle **Modo bulk** para trocar o campo de URL única por uma caixa de texto que aceita vários sites. Os sites podem ser separados por linha, vírgula, ponto e vírgula ou tabulação.

O lote é executado em sequência, com pausa aleatória entre um site e outro. Essa pausa é configurável em **Configurações → Modo bulk** e serve para evitar rajadas de requisições e deixar a análise mais gentil com os servidores analisados.

Configurações disponíveis:

- pausa mínima em segundos;
- pausa máxima em segundos;
- máximo de sites por lote;
- opção de parar o lote no primeiro erro fatal.

## 📁 Estrutura de Plugins

Cada plugin deve implementar:

```python
class MeuPlugin:
    def __init__(self):
        self.name = "nome_plugin"
        self.description = "Descrição"
        self.weight = 1.5  # Peso no score final
    
    def run(self, url: str) -> dict:
        return {
            "status": "ok",  # ou "error"
            "score": 85.5,   # 0-100
            "peso": self.weight,
            "erro": None,
            "detalhes": {
                "total_problemas": 5,
                "problemas": [...],
                "concorrentes": [
                    {
                        "nome": "Concorrente X",
                        "url": "https://...",
                        "score": 95,
                        "motivo": "Por que eles fazem melhor"
                    }
                ]
            }
        }
```

## 📊 Formato do data.json

```json
{
  "url": "https://exemplo.com",
  "inicio": "2025-12-25T02:48:54.034157",
  "plugins": {
    "ortografia": {
      "status": "ok",
      "score": 95.8,
      "peso": 1.5,
      "erro": null,
      "detalhes": {
        "total_erros": 12,
        "total_palavras": 1234,
        "taxa_erro": 0.97,
        "erros_principais": [...],
        "concorrentes": [...]
      }
    },
    "links": {...},
    "imagens": {...}
  },
  "score_final": 82.45,
  "ranking": "A (Muito bom)",
  "fim": "2025-12-25T02:52:15.123456"
}
```

## 🎨 Dashboard

O dashboard exibe:

### Visão Geral
- Score final em destaque
- Ranking (A-E)
- URL analisada
- Data da análise

### Gráficos
- **Radar Chart**: Comparação com concorrentes
- **Bar Chart**: Performance por categoria

### Cards de Análise

Cada categoria mostra:
1. **Métricas principais**: Números importantes
2. **Problemas detectados**: Com contexto e explicação
3. **Concorrentes**: 3 exemplos de quem faz melhor
4. **Links para exemplos**: Acesso direto aos sites

### Cores por Status
- 🟢 Verde: Score > 80 (Sucesso)
- 🟡 Amarelo: Score 60-80 (Atenção)
- 🔴 Vermelho: Score < 60 (Crítico)

## 🔌 Criar Novo Plugin

1. Crie pasta: `plugins/nome_plugin/`
2. Adicione `plugin.py`:

```python
class NomePlugin:
    def __init__(self):
        self.name = "nome_plugin"
        self.description = "O que faz"
        self.weight = 1.0
    
    def run(self, url: str) -> dict:
        # Sua análise aqui
        return {...}
```

3. Execute: O plugin será carregado automaticamente!

## 🎯 Exemplos de Uso

### Análise Rápida
```bash
python main.py https://example.com
```

### Análise Completa com Dashboard
```bash
# Terminal 1
python main.py https://example.com

# Terminal 2
python server/app.py
```

### Comparar Múltiplos Sites
```bash
python main.py https://pizzahut.com.br/
python main.py https://www.habibs.com.br/
python main.py https://site3.com
```

## 📈 Sistema de Pontuação

### Score Final
Calculado por média ponderada:

```
score_final = Σ(score_plugin × peso_plugin) / Σ(pesos)
```

### Rankings
- **A (90-100)**: Excelente
- **B (80-89)**: Muito bom
- **C (70-79)**: Bom
- **D (60-69)**: Regular
- **E (0-59)**: Precisa melhorias

## 🛠️ Troubleshooting

### Erro: "No module named 'requests'"
```bash
pip install requests
```

### Erro: Lighthouse não encontrado
```bash
npm install -g lighthouse
```

### Erro: LanguageTool
Requer Java instalado:
```bash
# Ubuntu/Debian
sudo apt install default-jre

# Windows
# Baixe do site oficial do Java
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie um plugin novo
3. Teste localmente
4. Envie PR com documentação

## 📝 TODO

- [ ] Cache de resultados
- [ ] Análise de velocidade de carregamento
- [ ] Verificação de segurança (HTTPS, headers)
- [ ] Análise de acessibilidade WCAG
- [ ] Exportar relatórios em PDF
- [ ] API REST para integração
- [ ] Agendamento de análises periódicas
- [ ] Notificações de mudanças

## 📄 Licença

MIT License - Use livremente!

## 🙏 Créditos

Ferramentas utilizadas:
- Bootstrap 5
- Chart.js
- Flask
- BeautifulSoup
- LanguageTool
- Lighthouse
- Pillow

---

**Desenvolvido com ❤️ para análise de qualidade web**

## Correção Lighthouse no Windows

Se aparecer `Lighthouse não está instalado`, mesmo depois de `npm install -g lighthouse`, normalmente o problema é o PATH do npm global no Windows.

Use:

```bat
npm prefix -g
where lighthouse
where lighthouse.cmd
python scripts\check_lighthouse.py
```

Os arquivos `setup.bat`, `run.bat` e `run_dashboard.bat` já ajustam temporariamente o PATH com `%APPDATA%\npm` e com o resultado de `npm prefix -g`. O plugin também tenta automaticamente `lighthouse`, `lighthouse.cmd`, `lighthouse.exe` e, por último, `npx --yes lighthouse`.

Se quiser forçar um caminho específico:

```bat
set LIGHTHOUSE_BIN=C:\Users\SEU_USUARIO\AppData\Roaming\npm\lighthouse.cmd
run_dashboard.bat
```

## Correção do `check_lighthouse.py`

Se aparecer este erro:

```txt
ImportError: cannot import name 'SocialMediaPlugin' from 'plugins.plugin'
```

Atualize para esta versão do projeto. A causa era um `plugins/__init__.py` antigo tentando importar o plugin de redes sociais pelo arquivo errado. O diagnóstico do Lighthouse agora carrega o plugin diretamente e não depende mais desse import frágil.

## Correção de falso erro do Lighthouse

Se o diagnóstico local disser OK:

```bat
python scripts\check_lighthouse.py
```

mas o painel continuar mostrando `Lighthouse não está instalado`, apague o resultado antigo:

```bat
python scripts\clear_output.py
```

O dashboard também possui os botões **Limpar resultado** e **Diagnosticar Lighthouse**. O primeiro remove `output/data.json`; o segundo valida o Lighthouse de dentro do próprio Flask.

## Correção desta versão

Esta versão corrige dois erros vistos no dashboard:

- Lighthouse: proteção para `score=None` retornado pelo Lighthouse 13 em alguns audits/categorias. Antes podia aparecer: `'<'' not supported between instances of 'NoneType' and 'float'`.
- Ortografia: compatibilidade com versões novas do `language-tool-python`, que podem usar `matched_text`/`rule_id` em vez de `matchedText`/`ruleId`.

Depois de atualizar, limpe o resultado antigo pelo botão **Limpar resultado** ou rode `clear_output.bat`, então execute uma nova análise.

## 🚂 Deploy no Railway + Supabase

Esta versão pode rodar com o mesmo código em dois modos:

- **local:** JSON em `output/`, como antes;
- **online:** PostgreSQL do Supabase quando `DATABASE_URL` estiver configurada.

Arquivos de deploy incluídos: `Dockerfile`, `railway.json`, `start.sh` e `Procfile`.
O container instala Chromium, Lighthouse, Node.js e Java para manter os plugins existentes.

Guia completo: [`docs/RAILWAY_SUPABASE.md`](docs/RAILWAY_SUPABASE.md)

Variáveis mínimas no Railway:

```env
DATABASE_URL=postgresql://...
STORAGE_BACKEND=database
STORAGE_STRICT=true
```

Para importar o histórico JSON existente para o Supabase:

```bash
python scripts/migrate_history_to_db.py
```
