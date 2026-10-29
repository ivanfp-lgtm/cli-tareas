# ADR-0001: Las acciones viven en acciones.json, no en el código

- Estado: aceptada
- Fecha: 2026-11-04
- Autor/a: Iván Gómez

## Contexto

Mi herramienta «tareas» automatiza tareas repetitivas con ficheros
(ordenar Descargas, renombrar fotos, limpiar temporales...). Cada persona
que la use tendrá carpetas y manías distintas, y yo mismo voy a querer
añadir acciones nuevas cada pocas semanas. En mi caso: mis 3 acciones
(ordenar-documentos, renombrar-fotos-movil y limpiar-capturas-viejas)
apuntan a rutas que cambié dos veces mientras probaba (~/Descargas real →
~/pruebas-tareas), y mi familia usará el mismo programa con sus propias
carpetas.

## Decisión

Las acciones se describen en un fichero JSON externo (acciones.json) con
un esquema documentado en el README. El código solo contiene el MOTOR que
lee, valida y ejecuta ese fichero. Añadir una acción = editar el JSON.

## Alternativas consideradas

1. Escribir cada acción como una función en Python.
   - A favor: cero parsing ni validación; el editor y el tipado avisan al escribir.
   - En contra: cada cambio exige tocar el código y volver a instalar; quien
     no programa no puede añadir acciones.
2. Usar YAML o TOML en vez de JSON.
   - A favor: más cómodo de escribir (comentarios, sin comillas dobles), TOML además encaja con pyproject.toml que ya uso.
   - En contra: exige una dependencia nueva (PyYAML / tomllib no parsea escritura en <3.11 y JSON ya está en la librería estándar); el curso fija "sin dependencias nuevas" esta semana.
3. Un mini-DSL propio ("mueve *.pdf a ~/Documentos/PDF" línea a línea).
   - A favor: lo entiende cualquiera sin saber JSON.
   - En contra: tocaría escribir y validar mi propio parser, mucho trabajo para la misma potencia que ya me da JSON.

## Consecuencias

- Positivas: añadir una acción no toca el código; el JSON se puede validar
  antes de ejecutar nada; el criterio de aceptación de cada acción se prueba
  con --simular; mi familia edita rutas sin abrir Python.
- Negativas: hay que mantener la validación al día cuando el esquema
  crezca (ya me pasó: tuve que añadir la validación de campos desconocidos);
  los errores de escritura en el JSON solo se ven al ejecutar validar; JSON
  no admite comentarios, así que el esquema tiene que estar bien documentado
  en el README.
- Qué haré si el esquema cambia: subir "version" a 2 y que config.cargar()
  rechace versiones desconocidas con un mensaje que lo diga (ya lo hace),
  escribiendo un ADR nuevo que sustituya a este.
