# Languini Snippets — Claude Code

Guarda estos fragmentos listos para pegar en Languini o en tus workflows. Incluyen las dos acciones oficiales de Claude Code con los valores mínimos para funcionar.

## Claude Code Action Official

```yaml
- name: Claude Code Action Official
  uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Claude Code Base Action

```yaml
- name: Claude Code Base Action
  uses: anthropics/claude-code-base-action@beta
  with:
    prompt: "Audit repository health and summarize open work."
    allowed_tools: "View,GlobTool,GrepTool,Bash(git:*)"
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Notas de uso

- **Secretos**: define `ANTHROPIC_API_KEY` en **Settings → Secrets → Actions**.
- **Permisos**: los workflows deben tener `contents`, `pull-requests`, `issues` y `id-token` en `write` para permitir commits y comentarios.
- **Ejecutar en manual**: usa `workflow_dispatch` para el Base Action si solo quieres lanzarlo bajo demanda.
