# Skill: Calculator (KYNIKOS Math Engine)

Permite evaluar expresiones matemáticas de forma segura usando la herramienta `calculate`.

## Uso

```
calculate(expression="2 + 2 * 10")
calculate(expression="(100 - 20) / 4")
calculate(expression="2^8")
```

## Operadores Soportados

- `+` Suma
- `-` Resta
- `*` Multiplicación
- `/` División
- `%` Módulo
- `^` Potencia (equivale a `**` en Python)
- `( )` Agrupación

## Restricciones

Solo se permiten operaciones numéricas. No se permite código arbitrario.

## Ejemplo

- Input: `expression="15 * 8 + (200 / 4)"`
- Output: `🧮 Resultado: 15 * 8 + (200 / 4) = 170`
