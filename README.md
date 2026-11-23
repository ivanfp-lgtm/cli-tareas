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
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida · 4 sin IA disponible (sin clave, sin red o servidor caído).
10. **Instalación:** `uv tool install --editable .` (desarrollo) o `uv tool install git+https://github.com/ivanfp-lgtm/cli-tareas` (desde GitHub).

## Instalación

Necesitas [uv](https://docs.astral.sh/uv/) (instala Python solo si hace falta).

```bash
# desde GitHub, con una orden (o usa una URL con @v1.0.0 para congelar la versión)
uv tool install git+https://github.com/ivanfp-lgtm/cli-tareas
tareas --help
tareas version        # debe decir: tareas 1.0.0
```

Mientras desarrollo, desde la carpeta del repo: `uv tool install --editable .`.
Si `tareas` no se encuentra: `uv tool update-shell`, cierra la terminal y ábrela otra vez.
Para desinstalar: `uv tool uninstall tareas`.

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
| `tipo`        | sí                 | `mover`·`copiar`·`renombrar`·`borrar`·`resumir`·`renombrar-ia`·`clasificar` | El motor elige la clase Python a partir de este campo. |
| `origen`      | no                 | ruta            | Carpeta por defecto si no pasas `CARPETA`. `~` se expande.     |
| `filtro`      | no                 | objeto          | Qué ficheros se tocan. Sin filtro = todos (¡cuidado con borrar!). |
| `destino`     | mover/copiar/clasificar | ruta       | A dónde van. Si no existe, se crea (solo al ejecutar de verdad). |
| `plantilla`   | renombrar          | texto con huecos | El nombre nuevo: `{fecha:%Y-%m-%d}`, `{n:03}`, `{ext}`, `{nombre}`. |
| `confirmar`   | no (destructivas: recomendado `true`) | `true`/`false` | Pide confirmación antes de actuar salvo que pases `--si`. |
| `instrucciones` | no (solo IA)      | texto           | El prompt de esa acción: lo que le pides al modelo. Configuración, no código. |
| `max_caracteres` | no (solo IA)     | entero 500–50000 | Tope de texto del documento que se manda al modelo (por defecto 12000). |
| `categorias`  | clasificar         | lista de textos | Las únicas respuestas válidas del modelo; lo demás va a `sin-clasificar`. |

### Filtros (dentro de `filtro`; si pones varios, se cumplen TODOS)

| Campo                  | Ejemplo                | Qué hace                                            |
|------------------------|------------------------|-----------------------------------------------------|
| `extensiones`          | `[".pdf", ".docx"]`    | Solo esas extensiones, en minúsculas (`FOTO.JPG` vale). |
| `patron`               | `"^captura.*\\.png$"`  | Expresión regular sobre el NOMBRE COMPLETO.          |
| `patron_nombre`        | `"^(IMG_|PXL_)"`       | Expresión regular sobre el nombre SIN extensión (para no liarla con mayúsculas). |
| `mas_antiguo_que_dias` | `30`                   | Solo ficheros modificados hace más de N días.        |
| `mayor_que_mb`         | `100`                  | Solo ficheros de más de N MB.                        |

En JSON la barra invertida de las regex se escribe doble (`"\\.png$"`).

### Acciones con IA (semana 3)

Los tipos `resumir`, `renombrar-ia` y `clasificar` preguntan a un modelo del centro
(la misma API que usa OpenCode). Cómo funcionan:

- La petición va en tres capas: el **sistema** (lo fija el código: reglas de formato y la
  frontera `<documento>…</documento>`), tus **instrucciones** (esto es configuración: se
  cambian en el JSON, sin tocar Python) y el **documento** (leído con `pypdf` si es PDF).
- `--simular` **no llama al modelo**: la tabla dice cuántos caracteres mandaría (~tokens).
- Lo que responde el modelo es una entrada más: `renombrar-ia` lo pasa por `a_nombre_seguro`
  (sin tildes, solo `[a-z0-9-]`, fuera la extensión, 60 caracteres) y `clasificar` solo
  acepta sus `categorias`; lo demás va a `sin-clasificar`.
- Como el modelo no es determinista, en acciones IA que cambian ficheros `confirmar` vale `true`.

### La IA y el modo sin red

La clave nunca está en el repo. Dos formas de configurarla (mira `.env.example`):

1. Exportando en tu terminal: `CENTRO_IA_URL`, `CENTRO_IA_KEY` y, si hace falta,
   `CENTRO_IA_CA` (certificado del instituto) y `CENTRO_IA_MODELO`.
2. `cp .env.example .env` y rellenarlo (`.env` está en `.gitignore` desde el primer commit).

`uv run tareas comprobar-ia` dice servidor, modelo y «clave: definida» (la clave nunca se
imprime) y hace una pregunta mínima al modelo. Si no hay clave, no hay red o el servidor
falla, las acciones con IA salen con **código 4** y un mensaje humano, y **las acciones sin
IA siguen funcionando**.

### Notas de comportamiento

- `--simular` enseña la misma tabla sin tocar NADA del disco (ni crea carpetas, ni llama al modelo).
- Nunca se sobrescribe: si el destino existe (o ya está reservado en la misma simulación) se añade el sufijo ` (1)`, ` (2)`…
- Al renombrar, si el nombre nuevo coincide con el actual, el fichero se marca `saltado`.
- Al renombrar cambiando SOLO mayúsculas (`FOTO1.JPG` → `foto1.jpg`): en un disco donde el rename se refleja de verdad (ext4, APFS sensible) se renombra normal; en uno donde no (NTFS, APFS insensible, un USB exfat) o cuando no se puede probar (sin permisos) se marca `saltado` y no se toca nada, porque ahí sería renombrar sobre sí mismo. Con `--simular` siempre se planifica como `saltado`.
- Códigos de salida: `0` bien · `1` fallo al ejecutar · `2` error de uso (lo pone Typer) · `3` configuración inválida · `4` sin IA disponible.

## Primeros pasos

1. Copia `acciones.json` de este repo en tu carpeta y cambia las rutas por las tuyas.
2. Comprueba que está bien: `tareas validar`
3. Mira qué haría, sin tocar nada: `tareas ejecutar ordenar-documentos --simular`
4. ¿IA? `tareas comprobar-ia` y después `tareas ejecutar resumir-apuntes --simular`.

## Mejoras apuntadas (para el futuro)

- Progreso con barra Rich cuando hay muchos ficheros.
- Orden `tareas deshacer` con un registro de lo hecho.
