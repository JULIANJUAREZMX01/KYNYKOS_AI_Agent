# Memoria compartida de agentes — KYNYKOS_AI_Agent

> Una sola bitácora para todos los agentes y herramientas. Léela antes de trabajar; agrega UNA entrada al terminar.
> Formato: fecha · área · problema · técnica · resultado. No dupliques. Esta memoria sobrevive aunque cambie la herramienta.

| Fecha | Área | Problema | Técnica aplicada | Resultado |
|---|---|---|---|---|
| 2026-11-03 | Seguridad | Inyección de comandos en `ToolHandlers`/`ToolExecutor` (PRs #12, #16, #19 abiertos 216-235 días). | Listas de argumentos, nunca `shell=True`; lista blanca de comandos. | Pendiente de merge: decidir cuál PR consolidar. |
| 2026-11-04 | UX / Accesibilidad | Pestañas inaccesibles y feedback bloqueante con alert() en dashboard. | Patrón WAI-ARIA tabs (role="tablist", role="tab", aria-selected, focus-visible rings), etiqueta explícita para textarea de memoria y retroalimentación en línea con aria-live="polite". | Navegación de pestañas accesible por teclado y guardado con estado de carga y mensaje de confirmación suave sin bloquear la interfaz. |
| 2026-11-06 | UX / Accesibilidad | Falta de navegación por flechas de teclado (WAI-ARIA roving tabindex) y contraste tenue en pestañas inactivas. | Implementación de navegación por teclas de flecha (ArrowLeft/ArrowRight/Home/End) con gestión dinámica de tabindex y contraste de texto optimizado (text-white para activa, text-gray-400 para inactivas). | Experiencia de navegación por teclado fluida y estándar WAI-ARIA para el dashboard web. |
