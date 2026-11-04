# Memoria compartida de agentes — KYNYKOS_AI_Agent

> Una sola bitácora para todos los agentes y herramientas. Léela antes de trabajar; agrega UNA entrada al terminar.
> Formato: fecha · área · problema · técnica · resultado. No dupliques. Esta memoria sobrevive aunque cambie la herramienta.

| Fecha | Área | Problema | Técnica aplicada | Resultado |
|---|---|---|---|---|
| 2026-11-03 | Seguridad | Inyección de comandos en `ToolHandlers`/`ToolExecutor` (PRs #12, #16, #19 abiertos 216-235 días). | Listas de argumentos, nunca `shell=True`; lista blanca de comandos. | Pendiente de merge: decidir cuál PR consolidar. |
| 2026-11-03 | Rendimiento | Redundancia en parsing y búsqueda regex en el hot path de `ConciergeAgentLoop.process_message`. | Precompilación de expresiones regulares a nivel módulo (`re.compile(..., re.I)`) en `SKILL_ROUTES` y extracción de argumentos. | Enrutamiento ~38% más rápido por mensaje evaluado (2.4s vs 3.8s en 10k iteraciones); 9 pruebas unitarias añadidas en `test_concierge_loop.py`. |
