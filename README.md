# fullstack-next-fast-template

Monólito fullstack com FastAPI no backend e frontend Next.js em construção, pensado para rodar em um único provedor com pipelines simples e integrações de IA.

## Visão Geral do Stack
- **Backend:** FastAPI (Python 3.11) com autenticação e integração assíncrona.
- **Frontend:** Next.js (em preparo) compartilhará a mesma versão do projeto.
- **Infra:** uv para dependências Python, Docker Compose para orquestração local, GitHub Actions para lint e testes.

## Primeiros Passos
1. Copie as variáveis padrão: `cp .env.example .env` (ajuste o que precisar antes de subir).
2. Instale dependências do backend: `make setup`.
3. Faça o build das imagens locais: `make docker-build`.
4. Suba os serviços: `make docker-up`.
5. Acompanhe os logs se necessário: `make docker-logs`.
6. Para desligar tudo: `make docker-down`.

> O comando `make setup` também cria o link simbólico esperado pelo Docker Compose. Assim, após o passo 1 você já tem o mínimo para subir a stack.

## Comandos Úteis do Makefile
- `make lint` – executa Black, Ruff e MyPy.
- `make test` – roda todos os testes com Pytest.
- `make migrate` – aplica migrações locais com Alembic.
- `make docker-restart` – reinicia os serviços do Compose mantendo dados.
- `make clean` – limpa caches e artefatos de lint/test.

Para adicionar dependências ou rodar os serviços manualmente, consulte os demais alvos descritos no `Makefile`.

## Versionamento
Mantemos uma única versão para todo o projeto no arquivo raiz `VERSION`:

```
0.0.1
```

Motivos da escolha:
- Você planeja deploys conjuntos (frontend + backend) em uma única máquina ou cluster, então uma versão sincronizada simplifica release notes, tags e futuras imagens Docker/Kubernetes.
- Evita divergências “frontend 1.x vs backend 2.x” em um contexto onde o deploy ainda não é isolado; quando o stack estiver mais maduro, dá para separar facilmente criando versões específicas.

Fluxo recomendado ao preparar uma nova versão:
1. Atualize `version.py` com a nova string sem remover o sufixo `__version__`.
2. Rode `make lint` e `make test` para validar a alteração.
3. Faça commit incluindo apenas o arquivo de versão (e eventuais mudanças relacionadas).
4. Opcional: crie uma tag Git (`git tag vX.Y.Z && git push --tags`) para alinhar pipelines e deploy.

O backend importa essa versão (via `src/version.py`) e o `pyproject.toml` usa o mesmo arquivo para empacotar. Quando o frontend estiver pronto, use o mesmo valor – por exemplo lendo o arquivo no build ou gerando um `version.ts` a partir dele.

## Próximos Passos
- Implementar o frontend consumindo a versão compartilhada.
- Preparar manifestos Docker/Kubernetes reaproveitando o arquivo de versão para nomear imagens.
