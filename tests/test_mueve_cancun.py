import pytest
from app.skills.mueve_cancun import (
    is_transport_query,
    get_route_info,
    format_route_response,
    get_generic_transport_response,
    POPULAR_ROUTES,
    APP_URL
)

def test_is_transport_query():
    """Test is_transport_query with various keywords and case sensitivity."""
    assert is_transport_query("¿Dónde hay un bus?") is True
    assert is_transport_query("quiero un Taxi") is True
    assert is_transport_query("boletos de ADO") is True
    assert is_transport_query("¿Cómo llego a la zona hotelera?") is True
    assert is_transport_query("hola, ¿cómo estás?") is False
    assert is_transport_query("comprar comida") is False

def test_get_route_info():
    """Test get_route_info returns correct route info or None."""
    # Test Aeropuerto to Centro
    result = get_route_info("aeropuerto centro")
    assert result == POPULAR_ROUTES["aeropuerto_centro"]

    # Test Tulum
    result = get_route_info("quiero ir a tulum")
    assert result == POPULAR_ROUTES["cancun_tulum"]

    # Test Aeropuerto to Zona Hotelera
    result = get_route_info("del aeropuerto al hotel")
    assert result == POPULAR_ROUTES["aeropuerto_zona_hotelera"]

    # Test Playa del Carmen
    result = get_route_info("bus a playa del carmen")
    assert result == POPULAR_ROUTES["cancun_playa"]

    # Test Zona Hotelera to Centro
    result = get_route_info("zona hotelera al centro")
    assert result == POPULAR_ROUTES["zona_hotelera_centro"]

    # Test unrecognized
    result = get_route_info("dame el clima")
    assert result is None

def test_format_route_response():
    """Test format_route_response returns formatted string with expected components."""
    route_info = POPULAR_ROUTES["aeropuerto_centro"]
    response = format_route_response(route_info)
    assert "Aeropuerto → Centro" in response
    assert APP_URL in response
    assert "🚌" in response

def test_get_generic_transport_response():
    """Test get_generic_transport_response returns default info string."""
    response = get_generic_transport_response()
    assert "**$13-15 MXN**" in response
    assert APP_URL in response
    assert "🚌" in response
