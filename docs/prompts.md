# Prompts clave del proyecto

## 2026-10-29 · Primera orden: listar (Sesión 1)
**Prompt del plan (agente plan):**
> Lee @README.md y @pyproject.toml. Quiero src/tareas/cli.py (app de Typer llamada app) y src/tareas/__main__.py con dos órdenes: version y listar [CARPETA]. No escribas código todavía: dime qué ficheros crearías...
> Criterio de aceptación: sin argumentos muestra ayuda en español; version imprime «tareas 0.1.0» leyendo __version__; listar pinta tabla Rich (Nombre, Tipo, Tamaño, Modificado), carpetas primero y luego alfabético sin distinguir mayúsculas; carpeta inexistente → stderr sin traza y código 1; vacía → aviso; pathlib, sin dependencias nuevas.

**Qué corregí del plan:** escapar los nombres con rich.markup.escape para que [borrador].pdf salga entero; saltar ficheros cuyo stat() falla (enlace roto/sin permisos) sin romper la tabla.
**Qué aprendí:** typer.Exit(code=1) termina con código 1 sin traza; los errores van a Console(stderr=True).

## 2026-11-03 · Validación de acciones.json (Sesión 2)
**Prompt:** Carga la skill acciones-json y lee @acciones.json. Quiero validar acciones.json ANTES de ejecutar nada: errores.py (TareasError/ConfigError/AccionNoValida), config.py con cargar(ruta) -> list[dict] y la orden «tareas validar». Criterio: JSON roto → línea y columna; cada mensaje dice QUÉ acción y QUÉ campo; sin traceback; sale con e.codigo_salida.

**Qué tuve que corregir:**
- El plan no detectaba CAMPOS DESCONOCIDOS en la acción (escribí «destinación» de prueba y validaba bien). Añadí la lista CAMPOS_ACCION.
- La validación de la plantilla probaba `plantilla.format(fecha="x", ...)`, pero `fecha` es un datetime; con `{fecha:%Y-%m-%d}` fallaba. Se valida con un datetime de verdad.
- Añadí la clave `patron_nombre` (regex sobre el nombre SIN extensión): mi patrón `^(IMG_|PXL_).*\.(jpg|...)$` no cogía IMG_0001.JPG porque el filtro de extensiones compara en minúsculas pero la regex veía `.JPG`.

## 2026-11-04 · Motor y clases (Sesión 2)
**Prompt:** Crea acciones.py (dataclass Resultado, base abstracta Accion con ejecutar/aplicar, fábrica desde_config con registro de subclases —nada de if/elif—, subclases Mover/Copiar/Renombrar/Borrar) y motor.py (Motor con seleccionar + ejecutar). Con simular=True no se toca NADA del disco. Nunca sobrescribir: sufijo « (1)».

**Qué tuve que corregir (caso traicionero del revisor):** dos ficheros que se renombran al MISMO nombre en una misma simulación: destino_libre miraba solo el disco y el segundo aplastaba al primero en la tabla. Solución: destino_libre recibe el conjunto `reservados` de destinos ya usados en esta pasada.

## 2026-11-04 · CLI: acciones / ejecutar / --config (Sesión 2)
**Prompt:** Amplía SOLO cli.py: opción global --config en @app.callback guardada en ctx.obj; «tareas acciones» (tabla); «tareas ejecutar NOMBRE [CARPETA] --simular --si» con confirmación en destructivas sin --si, resumen final y códigos 0/1/2/3 sin traceback.

**Qué tuve que corregir:** al contestar «n» a la confirmación, typer.abort() salía con un error feo de Click; capturo el Abort y salgo con código 1 y «Cancelado: no se ha tocado nada.» También desactivé el highlight de Rich en la consola de salida para que los nombres con corchetes no se pinten a trozos.

## Lo que me señaló @revisor y mi decisión
- «Dos ficheros al mismo destino en una simulación» → Arreglado (ver arriba).
- «ejecutar sin carpeta y sin origen usa la carpeta actual» → Lo dejo: es el comportamiento documentado del esquema (origen por defecto "."), y la tabla siempre muestra rutas absolutas antes de confirmar.
- «Borrar con confirmar:false no tiene sentido» → Lo mantengo: el esquema lo define así y sirve para temporales que borro a ciegas; --simular sigue siendo obligatorio en la rutina de pruebas.
