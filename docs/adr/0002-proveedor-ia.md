# ADR-0002: La IA va detrás de una interfaz (ProveedorIA)

- Estado: aceptada
- Fecha: 2026-11-12
- Autor/a: Iván Gómez

## Contexto

Mis acciones resumir, renombrar-ia y clasificar necesitan un modelo de lenguaje.
Hoy uso el servidor del centro (API de OpenAI, `CENTRO_IA_URL`), pero en casa o
el año que viene puede ser otro (por ejemplo Ollama con `ollama serve`), y en
las pruebas de la semana 4 no quiero depender de la red ni gastar tokens para
comprobar que mi código limpia bien una respuesta del modelo.

## Decisión

Toda llamada a un modelo pasa por la clase abstracta `ProveedorIA`
(`src/tareas/ia.py`), con un único método `completar(sistema, usuario)`.
`ProveedorCentro` la implementa con httpx hablando con el servidor del centro.
Las acciones (`src/tareas/acciones.py`) no saben qué servidor hay detrás: solo
conocen `completar()` y el `Motor` les pone el proveedor solo cuando hace falta
(ni `--simular` ni las acciones sin IA lo crean).

## Alternativas consideradas

1. Llamar a httpx directamente desde cada acción.
   - A favor: cero capas, menos líneas hoy.
   - En contra: duplicaría el manejo de errores (401, 429, timeouts, certificado)
     en cada acción; sin red no podría probar nada; cambiar de servidor
     significaría reescribir todas las acciones.
2. Usar la librería oficial de OpenAI (`uv add openai`).
   - A favor: menos código de HTTP a mano.
   - En contra: una dependencia más de la que solo uso una llamada; con httpx
     entiendo y audito cada línea (incluido el certificado con
     `ssl.create_default_context`, que la librería oficial gestiona peor con
     nuestra CA del instituto).
3. Un único proveedor global (función suelta, sin clase).
   - A favor: aún más simple.
   - En contra: imposible sustituirlo en las pruebas por un proveedor falso.

## Consecuencias

- Positivas: cambiar de servidor es escribir otra subclase; las pruebas de la
  semana 4 usan un `ProveedorFalso`, sin red y sin gastar un token; el modo sin
  red se resuelve en un sitio (`IANoDisponible`, sale con 4) y las acciones sin
  IA siguen funcionando.
- Negativas: una capa más que entender (una clase abstracta y un dataclass); el
  proveedor viaja «perezoso» por el Motor y hay que acordarse de ponerlo en la
  CLI solo cuando hace falta.
- La clave: vive en `.env` (ignorado por git desde el primer commit) o en
  variables de entorno que exporto yo; nunca en el repo, nunca impresa
  (`«_clave»` es privada y `comprobar-ia` solo dice «definida»), y
  `opencode.json` impide al agente leer `.env`.
