# Changelog

Todos los cambios que notará quien USA la herramienta. Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/) · versiones: [SemVer](https://semver.org/lang/es/).

## [1.0.0] - 2026-11-16

### Añadido

- Órdenes `tareas acciones`, `tareas validar` y `tareas ejecutar NOMBRE [CARPETA]`, con tabla de resultados, `--simular` y `--si`.
- Opción global `--config RUTA` para usar otro fichero de acciones.
- Filtro `patron_nombre` (regex sobre el nombre sin extensión): `FOTO.JPG` y `IMG_0001.JPG` ya no se escapan.
- Acciones con IA: `resumir`, `renombrar-ia` y `clasificar`, con los modelos del centro. Antes de usar la respuesta del modelo se limpia, para que no salgan nombres raros ni rutas peligrosas.
- `tareas comprobar-ia`: dice si hay IA disponible (sale con 4 si no la hay).
- `--simular` en las acciones con IA: dice cuántos caracteres mandaría, sin gastar.
- Modo sin red: si falta la clave o no hay conexión, un mensaje humano, salida con 4 y las acciones sin IA siguen funcionando.
- `.env.example` con las variables que hacen falta (`CENTRO_IA_URL`, `CENTRO_IA_KEY`, `CENTRO_IA_CA`, `CENTRO_IA_MODELO`).
- Instalación con una orden desde GitHub: `uv tool install git+https://github.com/ivanfp-lgtm/cli-tareas`.
- 36 pruebas automáticas que se ejecutan en Linux, Windows y macOS en cada push (GitHub Actions).

### Cambiado

- `renombrar-ia` y `clasificar` preguntan antes de cambiar ficheros (`confirmar: true`): el modelo no es determinista y dos ejecuciones pueden dar nombres distintos.
- Las acciones destructivas avisan en la confirmación de que «cambian o borran» ficheros, no solo de que borran.

### Arreglado

- Dos ficheros que se renombraban al mismo nombre en una misma simulación se aplastaban en la tabla; ahora cada destino se reserva.
- `renombrar-ia` ya no duplica la extensión si el modelo la añade (`redes-ip.pdf` → `redes-ip.pdf`, no `redes-ip-pdf.pdf`).
- `tareas listar` con nombres tipo `[borrador].pdf` se escapaba mal con Rich.
- Al rechazar la confirmación con `n`, la orden salía con un error feo de Click; ahora sale con 1 y «Cancelado: no se ha tocado nada.».
- `renombrar` en Windows y macOS fallaba al cambiar solo mayúsculas (`FOTO1.JPG` → `foto1.jpg`): el motor se creía que había colisión y mandaba el fichero a ` (1)`… y encima el rename con el nombre exacto del que ya está peta en Windows, así que se perdía el resultado. Ahora la norma «nunca sobrescribir» la garantizan los códigos de error del sistema (se avisan con un mensaje humano, no se aplasta nada), y en los sistemas que no distinguen mayúsculas el cambio se detecta como cambio de nombre, no como colisión.
- `renombrar-ia` en Windows: mismo arreglo, y ya no puede sobrescribir un fichero que no existía al planificar la pasada.
