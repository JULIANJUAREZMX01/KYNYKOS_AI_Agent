# Skill: DateTime Helper (KYNIKOS Time Oracle)

Proporciona la fecha y hora actual en cualquier zona horaria usando la herramienta `get_datetime`.

## Uso

```
get_datetime()                                    # Cancún (predeterminado)
get_datetime(timezone="America/Mexico_City")
get_datetime(timezone="UTC")
get_datetime(timezone="America/New_York")
```

## Parámetros

| Parámetro  | Default            | Descripción                        |
|------------|--------------------|------------------------------------|
| `timezone` | `America/Cancun`   | Zona horaria IANA (ej. UTC, etc.)  |

## Salida

Devuelve fecha, hora, día de la semana e ISO 8601 en la zona indicada.

## Ejemplo

- Input: `timezone="America/Cancun"`
- Output:
  ```
  🕐 Fecha y Hora Actual
  - Zona: America/Cancun
  - Fecha: 2026-02-21 (Sábado)
  - Hora: 10:33:18
  - ISO: 2026-02-21T10:33:18-05:00
  ```
