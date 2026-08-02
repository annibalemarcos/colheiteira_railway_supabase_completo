# Login administrativo simples

O dashboard agora exige autenticação antes de liberar qualquer tela ou API.

## Credenciais padrão

```text
Usuário: admin
Senha: 000000
```

Não existe cadastro, recuperação de senha ou criação de outros usuários.

## Rotas públicas

- `/login`
- `/health` — necessário para o healthcheck do Railway

Todas as demais rotas, incluindo `/api/*`, exigem sessão autenticada.

## Variáveis opcionais

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=000000
SECRET_KEY=uma-chave-longa-e-aleatoria
SESSION_COOKIE_SECURE=true
```

No Railway, `SESSION_COOKIE_SECURE` é ativado automaticamente quando a variável `RAILWAY_ENVIRONMENT` está presente. Para produção, configure obrigatoriamente uma `SECRET_KEY` longa no painel de variáveis.

## Sessão

- duração: 12 horas;
- cookie `HttpOnly`;
- `SameSite=Lax`;
- cache desativado para páginas e APIs sensíveis;
- logout disponível no menu lateral e no topo.
