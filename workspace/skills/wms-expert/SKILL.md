# Skill: WMS Expert (Diogenes.Dev Edition)

Esta skill te permite analizar estados y lógicas de Manhattan WMS y queries de DB2.

## Referencia de Estados Manhattan WMS

- **10**: Recepción Iniciada
- **50**: En Almacén / Disponible
- **90**: Embarcado / Cerrado
- **99**: Cancelado

## Herramientas de Análisis SQL (JAJA.DEV Standards)

Al analizar una query para Julian:

1. **Optimización de JOINs**: Verificar que use índices de DB2.
2. **Selectividad**: Evitar `SELECT *`.
3. **Legibilidad**: Alias claros, mayúsculas para palabras clave de SQL.

## Comandos Rápidos

- `analiza query` → Escanea el portapapeles o archivo actual en busca de SQL ineficiente.
- `estado i l p` → Explica el estado de un Inventario/Lote/Pedido en Manhattan.
