# tareas

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros.

## Spec (versión 0 · 26/10/2026)
1. **Problema:** cada semana pierdo tiempo ordenando Descargas a mano y renombrando fotos del móvil.
2. **Para quién:** para mí y para mi familia (que tiene el mismo desorden en Descargas).
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes de la semana 1:** `tareas --help`, `tareas version`, `tareas listar [CARPETA]`.
5. **Órdenes previstas:** `tareas acciones`, `tareas validar`, `tareas ejecutar NOMBRE --simular`.
6. **Mis 3 acciones (borrador):** ordenar-documentos, renombrar-fotos-movil, limpiar-capturas-viejas.
7. **Nunca hará:** borrar sin preguntar ni tocar ficheros fuera de la carpeta que le indique.
8. **Plataformas:** Linux primero; también Windows y macOS.
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
10. **Instalación:** `uv tool install --editable .` (lo completo en la semana 4).

## Instalación

```bash
uv tool install --editable .   # dentro de la carpeta cli-tareas
tareas --help                  # ya funciona en cualquier carpeta
```

Si `tareas` no se encuentra: `uv tool update-shell`, cierra la terminal y ábrela otra vez.

## Esquema de acciones.json

Fichero JSON en la raíz (o donde indiques con `--config RUTA`). El motor lo valida TODO antes de tocar el disco.

### Raíz

| Campo      | Obligatorio | Tipo   | Qué hace                                             |
|------------|-------------|--------|------------------------------------------------------|
| `version`  | sí          | entero | Versión del esquema. Ahora mismo solo se acepta `1`.  |
| `acciones` | sí          | lista  | Las acciones. Vacía o ausente = error de configuración (código 3). |

### Cada acción

| Campo         | Obligatorio        | Tipo            | Qué hace                                                        |
|---------------|--------------------|-----------------|------------------------------------------------------------------|
| `nombre`      | sí                 | texto sin espacios | Lo que escribes en `tareas ejecutar NOMBRE`. Único.          |
| `descripcion` | sí                 | texto           | Lo que enseña `tareas acciones`.                               |
| `tipo`        | sí                 | `mover`·`copiar`·`renombrar`·`borrar` | El motor elige la clase Python a partir de este campo. |
| `origen`      | no                 | ruta            | Carpeta por defecto si no pasas `CARPETA`. `~` se expande.     |
| `filtro`      | no                 | objeto          | Qué ficheros se tocan. Sin filtro = todos (¡cuidado con borrar!). |
| `destino`     | mover/copiar       | ruta            | A dónde van. Si no existe, se crea (solo al ejecutar de verdad). |
| `plantilla`   | renombrar          | texto con huecos | El nombre nuevo: `{fecha:%Y-%m-%d}`, `{n:03}`, `{ext}`, `{nombre}`. |
| `confirmar`   | no (borrar: sí)    | `true`/`false`  | Pide confirmación antes de actuar salvo que pases `--si`.      |

### Filtros (dentro de `filtro`; si pones varios, se cumplen TODOS)

| Campo                  | Ejemplo                | Qué hace                                            |
|------------------------|------------------------|-----------------------------------------------------|
| `extensiones`          | `[".pdf", ".docx"]`    | Solo esas extensiones, en minúsculas (`FOTO.JPG` vale). |
| `patron`               | `"^captura.*\\.png$"`  | Expresión regular sobre el NOMBRE COMPLETO.          |
| `patron_nombre`        | `"^(IMG_|PXL_)"`       | Expresión regular sobre el nombre SIN extensión (para no liarla con mayúsculas). |
| `mas_antiguo_que_dias` | `30`                   | Solo ficheros modificados hace más de N días.        |
| `mayor_que_mb`         | `100`                  | Solo ficheros de más de N MB.                        |

En JSON la barra invertida de las regex se escribe doble (`"\\.png$"`).

### Notas de comportamiento

- `--simular` enseña la misma tabla sin tocar NADA del disco (ni crea carpetas).
- Nunca se sobrescribe: si el destino existe (o ya está reservado en la misma simulación) se añade el sufijo ` (1)`, ` (2)`…
- Al renombrar, si el nombre nuevo coincide con el actual, el fichero se marca `saltado`.
- Códigos de salida: `0` bien · `1` fallo al ejecutar · `2` error de uso (lo pone Typer) · `3` configuración inválida.

## Mejoras apuntadas (para semanas futuras)

- Progreso con barra Rich cuando hay muchos ficheros.
- Orden `tareas deshacer` con un registro de lo hecho (semana 4+).
- Acción con IA que clasifique por contenido (semana 3).
