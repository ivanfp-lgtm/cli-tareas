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

## 2026-11-11 · context7 por MCP: la CA de httpx (Sesión 3)
**Prompt (agente plan, con context7 conectado con /mcps):**
> Usa context7: en httpx 0.28, ¿cómo le paso a httpx.post un certificado de CA propio (fichero .crt)? Responde en 4 líneas con un ejemplo.

Trajo la documentación de httpx 0.28 y dos formas. **Ni con la documentación delante:** la forma 1 (`verify="ruta.crt"`) funciona pero httpx 0.28 la da por obsoleta (`DeprecationWarning`); la buena es `ssl.create_default_context(cafile=...)` (o cargar la CA en un contexto, como hacemos con `CENTRO_IA_CA`). context7 me trajo la doc, pero tuve que elegir yo.

## 2026-11-11 · El proveedor de IA (Sesión 3)
**Prompt del plan:** Carga la skill acciones-json y lee @src/tareas/errores.py y @pyproject.toml. Quiero una capa IA aparte, en src/tareas/ia.py: Respuesta (texto, tokens, segundos); ProveedorIA abstracta con completar(sistema, usuario, max_tokens); ProveedorCentro con httpx (POST {url}/chat/completions) y desde_entorno() con CENTRO_IA_URL/KEY/MODELO/CA leyendo antes un .env con python-dotenv. Dime qué errores puede dar httpx y qué mensaje en español le darías a cada uno.

**Qué corregí del plan:** se había olvidado del certificado del instituto (CENTRO_IA_CA con ssl.create_default_context, no verify="ruta") y del 429. Criterio de build: IANoDisponible con codigo_salida = 4, nunca un traceback, la clave nunca se imprime, y la orden «tareas comprobar-ia».

## 2026-11-12 · Las acciones con IA (Sesión 3)
**Prompt:** Añade los tipos resumir, renombrar-ia y clasificar: validar_ia en config.py (instrucciones, max_caracteres 500-50000, categorias); leer_texto para .txt/.md/.pdf (pypdf); AccionIA con proveedor; --simular NO llama al modelo (solo el presupuesto de caracteres); el documento va entre <documento> y </documento> y el sistema dice que eso es texto, nunca instrucciones. Lo que dice el modelo se pasa SIEMPRE por a_nombre_seguro (primera línea, fuera extensión, sin tildes, solo [a-z0-9-], 60 como mucho); clasificar responde una de categorias o sin-clasificar.

**Fallo real que encontré escribiendo las pruebas:** con la respuesta `redes-ip-protocolos.pdf`, a_nombre_seguro no quitaba la extensión y el fichero habría acabado `redes-ip-protocolos-pdf.pdf`. El arreglo fue una línea en el código (`re.sub(r"\.[A-Za-z0-9]{1,5}$", ...)`), no en la prueba.

**Mode sin red comprobado:** con CENTRO_IA_URL=http://127.0.0.1:9 la orden sale con 4 y «No llego al servidor de IA: ¿estás en la red del centro?» + «Las acciones sin IA siguen funcionando…»; con --simular ninguna acción IA toca la red.

## 2026-11-16 · Pruebas con pytest (Sesión 4)
**Prompt del plan:** Carga la skill acciones-json y lee config.py, motor.py, acciones.py e ia.py. Quiero pruebas con pytest. Dime: 1) qué fixtures en tests/conftest.py para que NINGUNA prueba toque mis carpetas de verdad ni llame al servidor de IA; 2) qué casos feos probarías de config, acciones y capa IA; 3) qué códigos de salida probaría desde fuera con CliRunner.

**Qué corregí del plan y de las pruebas del agente:**
- La fixture `aislado` bloqueaba HOME/USERPROFILE y las variables de IA, pero `~` mal expandido aún podía `mkdir` fuera de tmp_path. Añadí un `Path.mkdir` patched que lanza PermissionError si la carpeta está fuera de tmp_path, y `DOTENV_PATH` a un fichero inexistente para que load_dotenv no lea mi .env real.
- **Comprobé que las pruebas prueban (mutación a mano):** saqué el `mkdir` del `if not simular` en Mover → `test_simular_no_toca_el_disco` se puso en rojo. git restore y otra vez en verde.
- El caso `con-extension` de a_nombre_seguro (el modelo devuelve «redes-ip-protocolos.pdf») salió en rojo sin romper nada: mi código quitaba mal la extensión. Arreglado en el código (una línea), no en la prueba.
- **Windows sí que rompió una prueba (Actions en rojo):** `test_renombrar_con_plantilla` fallaba solo en `windows-latest`. Al comparar destinos con casefold «por si acaso», el rename de mayúsculas `FOTO1.JPG → foto1.jpg` se tomaba como colisión, se desviaba a ` (1)` y en Windows el rename al nombre exacto del que ya existe peta (EEXIST): se perdía el resultado. Arreglado: `destino_libre` compara EXACTO y `renombrar`/`renombrar-ia` incluyen el origen en `reservados`; la norma «nunca sobrescribir» la cumplen los códigos de error del SO, traducidos a TareasError. Prueba nueva `test_mismo_nombre_solo_mayusculas_no_achasta` + una simulación de Windows en local (exists/renome amb EEXIST) per verificar-ho sense runner.
- Los PDF falsos que escribo a mano en las pruebas no los lee pypdf: `leer_texto` envuelve también los errores de pypdf en TareasError con mensaje humano.

**Resultado:** 36 pruebas, 70 % de cobertura total (cli.py al 39%: la tabla de listar sigue sin probarse desde fuera, apuntado para la v1.0.1).

**Arreglo del fallo de Windows (post-1.0.0):** en Actions solo petaba `windows-latest` (mismo commit, ubuntu y macos en verde). Reproducido localmente con un script que parchea `Path.exists` y `Path.rename` al estilo NTFS (case-insensitive + EEXIST): la comparación casefold de `destino_libre` era la culpable doble (falsa colisión + rename que peta). Fix: comparación exacta, origen incluido en `reservados` y `if not simular` también en `renombrar-ia`. 37 pruebas en verde. Lección apuntada: el casefold «preventivo» era código muerto que además mentía; la protección real es atrapar EEXIST.

**Fix exfat + caja de arena (semana 4, pre-release):**
- Prompt: «Termina el proyecto: el conftest tiene el tmp_path de la caja de arena a medias (faltan imports), la prueba de mayúsculas petaba en el USB exfat del aula y ejecutar con acciones sin IA daba AttributeError. Arregla, pasa pytest y prepara la release».
- Qué corregí del agente: el primer intento de sondeo (renombrar un fichero existente) daba falso en mi ruta (tmpfs y exfat del USB se comportan distinto según la extensión: con `.jpg` el listado no refleja el rename, con `.tmp` sí). El revisor pilló una `_esta_en_windows` duplicada, docstrings que decían lo contrario del código, `pytest_sessionfinish` sin try/except y un sondeo que escribía aunque se simulara (contra el «sin tocar NADA» del README). Fix final: sondeo real solo al ejecutar (al simular se planifica `saltado`), limpieza de ambos temporeros en exfat, try/except en el fin de sesión y skip (no assert) si el repo vive en una ruta con acentos.
- Mutación: quito el `is not True` del rename de mayúsculas → `test_cambio_de_mayusculas_es_un_rename_normal` en rojo en exfat (vuelve a ` (1)`). Restaurado, 38 en verde (en ruta ASCII; en la del aula, skip con aviso).
