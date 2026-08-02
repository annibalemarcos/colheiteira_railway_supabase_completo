# Deploy no Railway com banco no Supabase

O projeto agora usa persistência híbrida:

- **Local, sem `DATABASE_URL`:** continua lendo e gravando `output/data.json` e `output/history/*.json`.
- **Railway, com `DATABASE_URL`:** cria automaticamente as tabelas no PostgreSQL do Supabase e passa a usar o banco como fonte do histórico.

## 1. Criar o banco no Supabase

1. Crie ou abra um projeto no Supabase.
2. Clique em **Connect**.
3. Para um serviço web persistente no Railway, copie preferencialmente a URL do **Session pooler**, porta `5432`.
4. A URL pode começar com `postgres://` ou `postgresql://`; o app converte para o driver `psycopg` automaticamente.

Não é necessário executar SQL manual: as tabelas abaixo são criadas no primeiro boot:

- `colheiteira_analysis_results`
- `colheiteira_app_state`

## 2. Subir no Railway

### Pela CLI

```bash
railway login
railway init
railway up
```

### Pelo GitHub

1. Suba esta pasta para um repositório.
2. No Railway, escolha **Deploy from GitHub repo**.
3. O Railway detectará o `Dockerfile` automaticamente.

## 3. Variáveis do Railway

Cadastre no serviço:

```env
DATABASE_URL=postgresql://postgres.bdmrgvbohxdpjggjtkmt:psoV16xx6TztZ3cw@aws-0-us-east-2.pooler.supabase.com:5432/postgres
STORAGE_BACKEND=database
STORAGE_STRICT=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD=000000
SECRET_KEY=COLOQUE_UMA_CHAVE_LONGA_E_ALEATORIA
WEB_CONCURRENCY=1
GUNICORN_THREADS=8
GUNICORN_TIMEOUT=600
DB_USE_NULL_POOL=false
SESSION_COOKIE_SECURE=true
```

O Railway fornece `PORT` automaticamente. Não fixe a porta no painel.

Variáveis opcionais:

```env
WEB_CONCURRENCY=1
GUNICORN_THREADS=8
GUNICORN_TIMEOUT=600
DB_USE_NULL_POOL=false
SESSION_COOKIE_SECURE=true
```

Mantenha `WEB_CONCURRENCY=1`: os jobs e logs em andamento ficam na memória do processo. O banco persiste os resultados concluídos.

Se usar o pooler de transação na porta `6543`, o app ativa `NullPool` e desliga prepared statements automaticamente.


## 4. Login do painel

O app não possui cadastro. O acesso padrão é:

```text
Usuário: admin
Senha: 000000
```

O login protege o dashboard e todas as rotas `/api/*`. Somente `/login` e `/health` permanecem públicos. Defina uma `SECRET_KEY` longa no Railway para assinar os cookies de sessão.

## 5. Gerar domínio e validar

1. No Railway, abra **Settings > Networking** e gere um domínio.
2. O healthcheck já está configurado em `/health` pelo `railway.json`.
3. Abra:

```text
https://SEU-DOMINIO/health
```

O retorno deve mostrar:

```json
{
  "status": "ok",
  "storage": {
    "backend": "database",
    "persistent": true,
    "ok": true
  }
}
```

## 6. Importar o histórico local existente

No computador, configure `DATABASE_URL` no terminal e rode:

```bash
python scripts/migrate_history_to_db.py
```

No Windows PowerShell:

```powershell
$env:DATABASE_URL="SUA_URL_DO_SUPABASE"
$env:STORAGE_BACKEND="database"
python scripts/migrate_history_to_db.py
```

Para importar também `output/data.json`:

```bash
python scripts/migrate_history_to_db.py --include-latest
```

## 7. Rodar localmente como antes

Nada muda no uso normal:

```bat
setup.bat
run_dashboard.bat
```

ou no Linux/macOS:

```bash
bash scripts/setup.sh
./run_dashboard.sh
```

Sem `DATABASE_URL`, o backend será `files` e a porta padrão continuará sendo `5840`.

## Observações importantes

- Não coloque a senha do Supabase no código ou no Git; use Variables do Railway.
- Se a senha tiver caracteres reservados de URL, use a connection string fornecida pelo painel ou aplique URL encoding.
- O disco do Railway não deve ser tratado como histórico permanente. Os JSONs continuam sendo gerados como compatibilidade, mas online o banco é a fonte de verdade.
- O container inclui Chromium, Node.js, Lighthouse e Java para preservar os plugins atuais.
