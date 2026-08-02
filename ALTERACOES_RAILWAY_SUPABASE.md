# Alterações — Railway + Supabase

## Persistência

- Nova camada `core/storage.py`.
- Sem `DATABASE_URL`, mantém JSON local em `output/`.
- Com `DATABASE_URL`, usa PostgreSQL/Supabase.
- Criação automática das tabelas do banco.
- Histórico, último resultado, abertura de relatório, exportação e limpeza agora usam a camada de persistência.
- Suporte ao Session pooler (`5432`) e Transaction pooler (`6543`) do Supabase.
- Script `scripts/migrate_history_to_db.py` para importar os JSONs existentes.

## Railway

- `Dockerfile` com Python, Node.js, Chromium e Lighthouse; ortografia em Python puro.
- `railway.json` com Dockerfile, healthcheck `/health` e política de restart.
- `start.sh` com Gunicorn, porta dinâmica via `PORT` e um worker para manter os jobs em memória coerentes.
- `Procfile` como fallback.

## Compatibilidade local

- `run_dashboard.bat`, `run.bat`, `run_dashboard.sh` e `run.sh` continuam válidos.
- Porta local padrão continua `5840`.
- SQLAlchemy é opcional no modo de arquivos, então uma instalação local antiga ainda abre o app.
- `setup.bat` e os novos `setup.sh`/`scripts/setup.sh` instalam as dependências atualizadas.

## Testes executados

- Backend de arquivos: leitura, histórico, último resultado e exportação.
- Backend SQL: gravação, leitura, histórico, limpeza e exportação.
- Rotas Flask nos dois backends.
- Migração de histórico para banco SQL de teste.
- Compilação de todos os arquivos Python.

## Login administrativo simples

- Adicionada tela `/login`, sem cadastro.
- Credenciais padrão: usuário `admin` e senha `000000`.
- Dashboard e APIs exigem sessão autenticada.
- `/health` continua público para o Railway.
- Logout disponível no menu lateral e no topo do painel.
- Credenciais e chave de sessão podem ser definidas por `ADMIN_USERNAME`, `ADMIN_PASSWORD` e `SECRET_KEY`.
