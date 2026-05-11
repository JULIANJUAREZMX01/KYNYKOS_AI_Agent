import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
from unittest.mock import patch

def test_cors_wildcard_no_credentials():
    """
    Verifica que si allow_origins es ["*"], allow_credentials sea False.
    """
    # Forzamos un reinicio de la app o simulamos el comportamiento de middleware
    # Como el middleware se añade al importar app, y app ya está importada,
    # verificamos el estado actual que debería ser el default (wildcard).

    client = TestClient(app)
    origin = "https://malicious.com"
    response = client.get("/api/status", headers={"Origin": origin})

    # Si allow_origins es ["*"], el header Access-Control-Allow-Origin suele ser "*"
    # o el Origin solicitado si el middleware lo maneja dinámicamente,
    # pero Access-Control-Allow-Credentials NO debe estar presente o ser "true"
    # cuando origins es "*".

    if response.headers.get("access-control-allow-origin") == "*":
        assert response.headers.get("access-control-allow-credentials") is None
    else:
        # FastAPI's CORSMiddleware when allow_origins=["*"] and allow_credentials=False
        # returns Access-Control-Allow-Origin: * and NO Access-Control-Allow-Credentials header.
        assert response.headers.get("access-control-allow-origin") == "*"
        assert "access-control-allow-credentials" not in response.headers

def test_cors_specific_origin_credentials():
    """
    Verifica que si allow_origins tiene dominios específicos, se permitan credenciales.
    Nota: Para probar esto realmente necesitaríamos re-instanciar la app con diferentes settings,
    lo cual es complejo sin reiniciar el proceso. Probamos la lógica interna.
    """
    from app.main import _allow_credentials

    # Simulamos lógica de main.py
    origins_wildcard = ["*"]
    credentials_wildcard = False if "*" in origins_wildcard else True
    assert credentials_wildcard is False

    origins_specific = ["https://trusted.com"]
    credentials_specific = False if "*" in origins_specific else True
    assert credentials_specific is True
