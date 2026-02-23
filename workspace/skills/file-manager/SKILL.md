# Skill: File Manager (KYNIKOS File Sentinel)

Permite listar, leer y escribir archivos dentro del directorio de trabajo seguro usando las herramientas `list_files`, `read_file` y `write_file`.

## Herramientas

### `list_files`

Lista el contenido de un directorio.

```
list_files(directory=".")
list_files(directory="workspace/logic")
```

### `read_file`

Lee el contenido de un archivo de texto.

```
read_file(path="workspace/MEMORY.md")
read_file(path="config/settings.yml")
```

### `write_file`

Escribe (o sobreescribe) un archivo de texto.

```
write_file(path="workspace/notes.md", content="## Nota\n\nContenido aquí.")
```

## Restricciones de Seguridad

- Solo se permiten rutas dentro del `workspace_path` configurado.
- Activar **OVERDRIVE** permite acceder a rutas adicionales del sistema.

## Ejemplo

```
list_files(directory=".")
# 📂 . (3 elementos):
# 📁 logic
# 📄 MEMORY.md (4096 B)
# 📄 SOUL.md (2048 B)
```
