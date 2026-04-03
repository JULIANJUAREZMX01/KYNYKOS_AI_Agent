# Skill: Last30Days Research (Diogenes Radar)

Investiga tendencias tecnológicas de los últimos 30 días. Sin API keys.

## Fuentes

- **GitHub** — repos nuevos con más estrellas (API pública)
- **HackerNews** — top stories (API Firebase pública)
- **Dev.to** — artículos técnicos recientes (API pública)

## Uso

```
[SKILL: last30days(topic=rust wasm)]
[SKILL: last30days(topic=ai agents, source=hackernews)]
[SKILL: last30days(topic=fastapi, source=github_trending)]
```

## Parámetros

| Parámetro | Default | Opciones |
|-----------|---------|----------|
| `topic`   | ai agents | cualquier tema técnico |
| `source`  | all | `all` \| `github_trending` \| `hackernews` \| `devto` |

## Ejemplo

Mensaje: "¿Qué hay de nuevo en Rust los últimos 30 días?"
Resultado: Lista de repos trending, artículos HN y Dev.to sobre Rust.

## Dependencias externas

**Ninguna.** Todas las fuentes son APIs públicas sin autenticación.
