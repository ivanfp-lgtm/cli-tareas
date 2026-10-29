---
name: acciones-json
description: Reglas del fichero acciones.json de la CLI tareas (campos, tipos, filtros, plantillas y validación). Úsala siempre que crees o cambies acciones o el código que las lee.
---
# Esquema de acciones.json
- Raíz: {"version": 1, "acciones": [...]}. Cada acción: nombre (único, minúsculas-con-guiones), descripcion, tipo.
- Tipos: mover y copiar (requieren destino), renombrar (requiere plantilla), borrar (siempre pide confirmación salvo --si).
- filtro opcional: extensiones (lista, en minúsculas), patron (regex válida sobre el nombre completo), patron_nombre (regex válida sobre el nombre sin extensión), mas_antiguo_que_dias, mayor_que_mb.
- plantilla: huecos {fecha:%Y-%m-%d}, {n:03}, {ext}, {nombre}.
- Campos desconocidos en la acción o en el filtro = error de validación.
## Reglas al programar
- Valida el JSON en config.py ANTES de ejecutar; errores con AccionNoValida(accion, campo, motivo).
- pathlib y shutil; encoding="utf-8"; nunca shell=True; nunca sobrescribir (destino_libre, también dentro de una simulación).
- Toda acción admite --simular y devuelve list[Resultado].
- Si añades un campo o un tipo nuevo, documéntalo en el README y en esta skill.
