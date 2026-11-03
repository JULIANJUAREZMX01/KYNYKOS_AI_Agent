# AGENTS.md — KYNIKOS AI Agent

> Fuente única de verdad para cualquier agente de IA en este repositorio (Jules, Claude Code, Copilot, Gemini, Codex, Antigravity, KynicOS).
> Dueño: Julián Juárez (@JAJA.DEV) · Marca de servicios: UNT Tecnologías Computacionales Cancún.
> Última revisión: 3 de noviembre de 2026.

## 1. Qué es este proyecto y para quién

**Producto.** Operador personal de Julián: agente de IA que conversa por Telegram y canales, ejecuta herramientas en su máquina y automatiza tareas de sus proyectos (Cantabria, MueveCancún, Kalpixk). Es la mano derecha operativa, no un producto para clientes.

**Usuarios.** Julián, un solo usuario humano. No hay multiusuario ni registro público.

**Estado.** Activo en desarrollo. Corre en local y en contenedor; depende de Base44/Telegram para el canal.

**Persona asignada.** sentinel · seguridad. Prioridad absoluta: cerrar inyecciones de comandos y endurecer permisos.

## 2. Cómo está construido

- **Lenguaje principal:** Python
- **Rama por defecto:** `main`
- **Estructura de primer nivel:** `.github`, `.github/workflows`, `app`, `app/agents`, `app/channels`, `app/cloud`, `app/concierge`, `app/config`, `app/core`, `app/services`

Python 3.11+ con FastAPI. Router multi-LLM en `app/agents/`, canales en `app/channels/`, herramientas en `app/core/tools.py`, integraciones cloud en `app/cloud/`, personas en `app/concierge/persona.py`.

### Trampas conocidas (esto es lo que más tiempo cuesta)

- `app/core/tools.py` ejecuta comandos del sistema. Es la superficie de ataque más peligrosa del repo: cualquier cambio ahí exige revisión de seguridad.
- Existe un `overdrive_mode` que salta los filtros de seguridad; nunca lo actives por defecto ni en pruebas.
- El puente de WhatsApp (`app/cloud/whatsapp_bridge.py`) abre una sesión: no lo inicialices en pruebas automatizadas.
- Los comandos de apagado/reinicio usan `os.system` y son específicos de Windows.

## 3. Método de trabajo (obligatorio)

1. **Plan primero.** Antes de tocar código, escribe el plan en 3 a 6 puntos y espera aprobación. Sin plan no hay cambio.
2. **Un cambio, un propósito.** Un PR resuelve una cosa. Si descubres otra, se anota en `docs/agentes/MEMORIA.md` y se atiende después.
3. **Radio de explosión pequeño.** Máximo 8 archivos y 300 líneas por PR. Si el cambio es mayor, se parte.
4. **Reversibilidad.** Todo cambio debe poder revertirse con un `git revert` limpio. No reescribas historia ni fuerces push.
5. **Verifica antes de decir que terminaste.** Ejecuta los comandos de la sección 5 y pega el resultado real. "Debería funcionar" no es un resultado.
6. **Si algo falla, revierte.** No dejes el repo en rojo intentando arreglarlo a ciegas.
7. **Deja memoria.** Cada cambio añade una entrada a `docs/agentes/MEMORIA.md`: fecha, qué se cambió, por qué, cómo se verificó.
8. **Nunca mergees.** Abres el PR y lo enlazas. Julián decide.

## 4. Prohibiciones duras

- **Secretos**: nunca escribas tokens, llaves, PINs, contraseñas ni cadenas de conexión en el código, en commits, en logs ni en el texto del PR. Si encuentras uno expuesto, no lo copies: avísalo en el PR como riesgo.
- **Datos de personas**: nada de nombres, teléfonos, correos, CURP, RFC o datos de huéspedes/clientes en código, pruebas o fixtures. Usa datos inventados con etiqueta clara.
- **Dependencias nuevas**: no añadas librerías sin justificarlo y sin aprobación explícita. Prefiere la biblioteca estándar.
- **Subidas de versión mayores**: no actualices el framework principal ni cambies de versión mayor de Node/Python por iniciativa propia; rompe despliegues.
- **Refactors masivos**: nada de renombrar directorios, mover archivos o reformatear todo el repo de golpe.
- **Tocar la CI para "que pase"**: no desactives pruebas, no pongas `continue-on-error` ni borres pasos de los workflows para salir del rojo.
- **Merge, force push, borrar ramas ajenas, tocar `main` directamente.**

- No añadas ejecución de comandos nuevos sin lista blanca de argumentos.
- No registres el contenido de conversaciones privadas en logs persistentes.

## 5. Verificación y definición de terminado

**Comandos de verificación** (desde la raíz, en este orden):

```bash
pip install -r requirements.txt
pytest -q
ruff check .
```

Si un comando falla por el entorno y no por tu cambio, dilo en el PR en vez de silenciarlo.

Un cambio está terminado cuando, y solo cuando:

- Los comandos de verificación corren sin error y pegaste su salida real.
- No añadiste configuración ni credenciales nuevas.
- Actualizaste `docs/agentes/MEMORIA.md`.
- El PR explica qué cambia, por qué, cómo se probó y qué podría romperse.
- Si tocaste algo visible al usuario, describiste cómo comprobarlo a mano.

## 6. Glosario del dominio

- **persona**: Perfil de comportamiento del agente (tono, límites, especialidad).
- **skill**: Acción concreta registrada y ejecutable por el agente.
- **overdrive**: Modo que desactiva las protecciones de comandos peligrosos.

## 7. Dónde está el resto del contexto

- `docs/agentes/MEMORIA.md` — bitácora de cambios y aprendizajes.
- `docs/adr/` — decisiones de arquitectura con su motivo.
- `docs/COLA.md` (en el portafolio) — qué está en turno y qué espera.
- `docs/AGENTES.md` (en el portafolio) — reglas comunes a todos los repositorios.

## 8. Cómo pedir ayuda

Si el plan no cabe en las reglas anteriores, no improvises: deja el PR en borrador explicando el bloqueo y qué decisión necesitas de Julián.
