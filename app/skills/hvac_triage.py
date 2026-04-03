"""
KynicOS — Skill: HVAC Triage
Diagnóstico técnico Fan & Coil. Diferenciador vs competencia.
"""
from typing import Dict, Tuple, Optional

HVAC_KB: Dict[str, Dict] = {
    "no_enfria": {
        "descripcion": "AC no enfría / aire caliente",
        "diagnostico": ["🔍 Filtro saturado (causa más común) — limpieza, 30min", "🔍 Refrigerante bajo — técnico certificado", "🔍 Compresor falla — emergencia"],
        "prioridad": "media", "eta_minutos": 30,
    },
    "ruido_raro": {
        "descripcion": "Sonido extraño en el AC",
        "diagnostico": ["🔧 Paletas del fan golpeando — ajuste menor", "🔧 Vibración del compresor — posible falla", "🔧 Bloque de hielo en evaporador"],
        "prioridad": "baja", "eta_minutos": 45,
    },
    "gotea_agua": {
        "descripcion": "AC gotea agua",
        "diagnostico": ["💧 Drenaje tapado — limpieza inmediata", "💧 Bandeja condensados llena", "💧 Exceso de humedad (normal en Cancún)"],
        "prioridad": "alta", "eta_minutos": 20,
    },
    "no_enciende": {
        "descripcion": "AC no enciende",
        "diagnostico": ["⚡ Control sin batería — reemplazar pilas", "⚡ Breaker disparado — reset tablero eléctrico", "⚡ Falla tarjeta electrónica — técnico"],
        "prioridad": "alta", "eta_minutos": 15,
    },
}

KEYWORD_MAP = {
    "no enfría": "no_enfria", "no enfriar": "no_enfria", "aire caliente": "no_enfria",
    "calor": "no_enfria", "ruido": "ruido_raro", "sonido": "ruido_raro",
    "gotea": "gotea_agua", "agua": "gotea_agua", "no enciende": "no_enciende",
    "no prende": "no_enciende", "no funciona": "no_enciende",
}

def detect_hvac_issue(message: str) -> Tuple[Optional[str], Optional[Dict]]:
    msg_lower = message.lower()
    hvac_kw = ["aire", "ac", "a/c", "clima", "acondicionado", "frio", "frío"]
    if not any(k in msg_lower for k in hvac_kw):
        return None, None
    for kw, key in KEYWORD_MAP.items():
        if kw in msg_lower:
            return key, HVAC_KB[key]
    return "unknown", {"descripcion": "Problema con AC", "diagnostico": ["Más detalles necesarios"], "prioridad": "media", "eta_minutos": 30}

def generate_hvac_response(symptom_key: str, issue_data: Dict, room: str = "su habitación") -> str:
    if symptom_key == "unknown":
        return f"Reporte de AC en {room} recibido. 🔧\n¿El AC no enfría, hace ruido, gotea o no enciende?"
    prioridad = issue_data.get("prioridad", "media")
    eta = issue_data.get("eta_minutos", 30)
    urgencia = "🔴 *Prioridad alta*" if prioridad == "alta" else "🟡 *Prioridad media*"
    return (
        f"Reporte: _{issue_data['descripcion']}_ en {room}\n\n"
        f"{urgencia} — Técnico asignado\nETA: **{eta} min**\n\n"
        f"{issue_data['diagnostico'][0]}\n\n¿Necesita cambio de habitación mientras tanto?"
    )

def get_ticket_priority(symptom_key: str) -> str:
    return HVAC_KB.get(symptom_key, {}).get("prioridad", "media")
