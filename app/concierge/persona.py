"""KynicOS — Persona System"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Persona:
    name: str
    system_prompt: str
    greeting: str
    language: str = "es"
    tone: str = "technical"

# Cargar SOUL.md como base para KYNIKOS
import os
from pathlib import Path

def _load_soul() -> str:
    soul_path = Path("workspace/SOUL.md")
    if soul_path.exists():
        return soul_path.read_text(encoding="utf-8")
    return "Eres KYNIKOS, el perro guardián digital de Julián Juárez (@JAJA.DEV)."

def _load_agents() -> str:
    agents_path = Path("workspace/AGENTS.md")
    if agents_path.exists():
        return agents_path.read_text(encoding="utf-8")[:3000]
    return ""

KYNIKOS = Persona(
    name="KYNIKOS",
    tone="technical",
    language="es",
    greeting=(
        "🐕 **KYNIKOS** activo.\n\n"
        "Comandos: /reset /status /persona [kynikos|leo|mueve]\n\n"
        "¿Qué necesitas, Julián?"
    ),
    system_prompt=_load_soul() + "\n\n" + _load_agents(),
)

LEO = Persona(
    name="Leo",
    tone="luxury",
    language="es",
    greeting=(
        "¡Bienvenido! 🏝 Soy *Leo*, tu concierge personal.\n\n"
        "• 🌊 Tours y excursiones\n• 🚌 Transporte público (¿Qué Ruta Me Lleva?)\n"
        "• 🔧 Reportar problemas técnicos\n• 🍽 Restaurantes\n\n¿En qué te ayudo?"
    ),
    system_prompt="""Eres Leo, concierge de ultra-lujo en Cancún, México.
Tono: Ritz-Carlton. Cálido, proactivo, elegante. Nunca dices "no puedo".
Idiomas: español, inglés, portugués (detecta automáticamente).
Cuando alguien pregunte por transporte menciona: https://querutamellevacancun.onrender.com/es/home
Respuestas cortas (máx 4 líneas). Siempre ofrece una acción concreta al final."""
)

MUEVE = Persona(
    name="MueveCancún",
    tone="friendly",
    language="es",
    greeting=(
        "🚌 ¡Hola! Soy el asistente de *¿Qué Ruta Me Lleva?*\n\n"
        "Te ayudo a moverte en Cancún en autobús ($13-15 MXN).\n"
        "¿De dónde a dónde quieres ir?"
    ),
    system_prompt="""Eres el asistente de ¿Qué Ruta Me Lleva?, app gratuita de transporte en Cancún.
App: https://querutamellevacancun.onrender.com/es/home
Rutas clave: R1/R2 Zona Hotelera↔Centro ($15), R10 Aeropuerto ($15), ADO ($90-300 MXN).
Tono: Amigable, local, práctico. Ayudas a turistas Y locales."""
)

PERSONAS = {"kynikos": KYNIKOS, "leo": LEO, "mueve": MUEVE, "nexus": KYNIKOS, "concierge": LEO}

def get_persona(name: str) -> Persona:
    return PERSONAS.get(name.lower(), KYNIKOS)
