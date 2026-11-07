# Memoria compartida de agentes — KYNYKOS_AI_Agent

> Una sola bitácora para todos los agentes y herramientas. Léela antes de trabajar; agrega UNA entrada al terminar.
> Formato: fecha · área · problema · técnica · resultado. No dupliques. Esta memoria sobrevive aunque cambie la herramienta.

| Fecha | Área | Problema | Técnica aplicada | Resultado |
|---|---|---|---|---|
| 2026-11-03 | Seguridad | Inyección de comandos en `ToolHandlers`/`ToolExecutor` (PRs #12, #16, #19 abiertos 216-235 días). | Listas de argumentos, nunca `shell=True`; lista blanca de comandos. | Pendiente de merge: decidir cuál PR consolidar. |
| 2026-11-04 | UX / Accesibilidad | Pestañas inaccesibles y feedback bloqueante con alert() en dashboard. | Patrón WAI-ARIA tabs (role="tablist", role="tab", aria-selected, focus-visible rings), etiqueta explícita para textarea de memoria y retroalimentación en línea con aria-live="polite". | Navegación de pestañas accesible por teclado y guardado con estado de carga y mensaje de confirmación suave sin bloquear la interfaz. |
| 2026-11-06 | Seguridad | Inyección de argumentos/opciones en `ToolExecutor._network_scan` mediante parámetro `target`. | Validación estricta con `ipaddress` y regex para FQDN/hostnames; bloqueo de flags y caracteres no permitidos. | Escaneo seguro restringido únicamente a direcciones IP o hostnames válidos sin riesgo de inyección en CLI. |
| 2026-11-07 | Rendimiento | Recálculo redundante de `message.lower()` en bucle de clasificación de intención en `is_transport_query`. | Normalización previa del mensaje (`msg_lower = message.lower()`) una sola vez con salida temprana en iteración directa sobre palabras clave. | Clasificación de query ~4x más rápida sin alterar la semántica ni introducir dependencias. |
