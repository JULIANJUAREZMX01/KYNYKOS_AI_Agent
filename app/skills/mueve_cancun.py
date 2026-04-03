"""KynicOS — Skill: MueveCancún Integration"""

APP_URL = "https://querutamellevacancun.onrender.com/es/home"

POPULAR_ROUTES = {
    "aeropuerto_zona_hotelera": {"nombre": "Aeropuerto → Zona Hotelera", "opciones": [{"tipo": "ADO", "precio": "$150 MXN", "tiempo": "15 min"}, {"tipo": "Taxi oficial", "precio": "$250-350 MXN", "tiempo": "10 min"}]},
    "aeropuerto_centro": {"nombre": "Aeropuerto → Centro", "opciones": [{"tipo": "ADO", "precio": "$150 MXN", "tiempo": "10 min"}, {"tipo": "R10 bus", "precio": "$15 MXN", "tiempo": "20 min"}]},
    "cancun_tulum": {"nombre": "Cancún → Tulum", "opciones": [{"tipo": "ADO", "precio": "$140-200 MXN", "tiempo": "2h"}, {"tipo": "Colectivo", "precio": "$60-80 MXN", "tiempo": "2h30m"}]},
    "cancun_playa": {"nombre": "Cancún → Playa del Carmen", "opciones": [{"tipo": "ADO", "precio": "$90-120 MXN", "tiempo": "1h15m"}]},
    "zona_hotelera_centro": {"nombre": "Zona Hotelera → Centro", "opciones": [{"tipo": "R1/R2 bus", "precio": "$15 MXN", "tiempo": "30-45 min"}]},
}

TRANSPORT_KW = ["autobús","bus","ruta","transporte","cómo llego","como llego","cómo ir","como ir","taxi","combi","ado","colectivo","moverse","r1","r2","r10","zona hotelera","aeropuerto","playa del carmen","tulum","chichen"]

def is_transport_query(message: str) -> bool:
    return any(k in message.lower() for k in TRANSPORT_KW)

def get_route_info(message: str):
    m = message.lower()
    if "aeropuerto" in m and ("zona hotelera" in m or "hotel" in m): return POPULAR_ROUTES["aeropuerto_zona_hotelera"]
    if "aeropuerto" in m and "centro" in m: return POPULAR_ROUTES["aeropuerto_centro"]
    if "tulum" in m: return POPULAR_ROUTES["cancun_tulum"]
    if "playa del carmen" in m: return POPULAR_ROUTES["cancun_playa"]
    if ("zona hotelera" in m or "hotel" in m) and "centro" in m: return POPULAR_ROUTES["zona_hotelera_centro"]
    return None

def format_route_response(route_info) -> str:
    lines = [f"🚌 *{route_info['nombre']}*\n"]
    for op in route_info["opciones"]:
        lines.append(f"• *{op['tipo']}* — {op['precio']} | ⏱ {op['tiempo']}")
    lines.append(f"\n📱 App gratuita de rutas:\n{APP_URL}")
    return "\n".join(lines)

def get_generic_transport_response() -> str:
    return (f"Para moverte en Cancún el transporte público cuesta **$13-15 MXN** 🚌\n\n"
            f"Dime: ¿de dónde a dónde quieres ir?\n\nApp gratuita: {APP_URL}")
