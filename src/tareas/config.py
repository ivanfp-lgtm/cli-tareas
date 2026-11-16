# src/tareas/config.py
"""Carga y valida acciones.json ANTES de tocar el disco."""

import json
import re
from datetime import datetime
from pathlib import Path

from .errores import AccionNoValida, ConfigError

TIPOS = {"mover", "copiar", "renombrar", "borrar", "resumir", "renombrar-ia", "clasificar"}
TIPOS_IA = {"resumir", "renombrar-ia", "clasificar"}
OBLIGATORIOS = ["nombre", "descripcion", "tipo"]
POR_TIPO = {
    "mover": "destino",
    "copiar": "destino",
    "renombrar": "plantilla",
    "clasificar": "categorias",
}
CAMPOS_ACCION = {
    "nombre",
    "descripcion",
    "tipo",
    "origen",
    "filtro",
    "destino",
    "plantilla",
    "confirmar",
    "instrucciones",
    "max_caracteres",
    "categorias",
}
FILTROS_VALIDOS = {"extensiones", "patron", "patron_nombre", "mas_antiguo_que_dias", "mayor_que_mb"}


def _validar_filtro(accion: dict, nombre: str) -> None:
    filtro = accion.get("filtro")
    if filtro is None:
        return
    if not isinstance(filtro, dict):
        raise AccionNoValida(nombre, "filtro", "debe ser un objeto")
    for clave in filtro:
        if clave not in FILTROS_VALIDOS:
            raise AccionNoValida(
                nombre,
                f"filtro.{clave}",
                f"no existe; usa uno de: {', '.join(sorted(FILTROS_VALIDOS))}",
            )
    extensiones = filtro.get("extensiones")
    if extensiones is not None:
        if not isinstance(extensiones, list) or not all(
            isinstance(e, str) for e in extensiones
        ):
            raise AccionNoValida(
                nombre, "filtro.extensiones", "debe ser una lista de textos"
            )
    for clave in ("patron", "patron_nombre"):
        valor = filtro.get(clave)
        if valor is None:
            continue
        if not isinstance(valor, str):
            raise AccionNoValida(nombre, f"filtro.{clave}", "debe ser un texto")
        try:
            re.compile(valor)
        except re.error as e:
            raise AccionNoValida(
                nombre, f"filtro.{clave}", f"expresión regular rota: {e}"
            ) from e
    for clave in ("mas_antiguo_que_dias", "mayor_que_mb"):
        valor = filtro.get(clave)
        if valor is not None and (
            not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor < 0
        ):
            raise AccionNoValida(nombre, f"filtro.{clave}", "debe ser un número ≥ 0")


def validar_ia(nombre: str, a: dict) -> None:
    """Los campos de las acciones con IA: instrucciones, max_caracteres y categorias."""
    if "instrucciones" in a and not isinstance(a["instrucciones"], str):
        raise AccionNoValida(nombre, "instrucciones", "tiene que ser un texto")
    tope = a.get("max_caracteres", 12000)
    if not isinstance(tope, int) or isinstance(tope, bool) or not 500 <= tope <= 50000:
        raise AccionNoValida(
            nombre, "max_caracteres", "tiene que ser un entero entre 500 y 50000"
        )
    if "categorias" in a:
        cats = a["categorias"]
        if (
            not isinstance(cats, list)
            or not cats
            or not all(isinstance(c, str) and c for c in cats)
        ):
            raise AccionNoValida(
                nombre, "categorias", "tiene que ser una lista de textos no vacía"
            )
    if "destino" in a and not isinstance(a["destino"], str):
        raise AccionNoValida(nombre, "destino", "debe ser un texto")


def _validar_accion(accion: dict, vistos: set[str]) -> None:
    if not isinstance(accion, dict):
        raise ConfigError("Cada acción debe ser un objeto con campos")
    nombre = accion.get("nombre") or f"nº {len(vistos) + 1}"
    if not isinstance(nombre, str):
        raise AccionNoValida(str(nombre), "nombre", "debe ser un texto")
    for campo in accion:
        if campo not in CAMPOS_ACCION:
            raise AccionNoValida(
                nombre,
                campo,
                f"no existe; usa uno de: {', '.join(sorted(CAMPOS_ACCION))}",
            )
    for campo in OBLIGATORIOS:
        if not accion.get(campo):
            raise AccionNoValida(nombre, campo, "es obligatorio")
    if " " in nombre:
        raise AccionNoValida(nombre, "nombre", "no puede llevar espacios")
    if nombre in vistos:
        raise AccionNoValida(nombre, "nombre", "está repetido")
    vistos.add(nombre)
    tipo = accion["tipo"]
    if tipo not in TIPOS:
        raise AccionNoValida(
            nombre, "tipo", f"«{tipo}» no existe; usa uno de: {', '.join(sorted(TIPOS))}"
        )
    extra = POR_TIPO.get(tipo)
    if extra and not accion.get(extra):
        raise AccionNoValida(
            nombre, extra, f"es obligatorio en acciones de tipo {tipo}"
        )
    if tipo == "clasificar" and not accion.get("destino"):
        raise AccionNoValida(
            nombre, "destino", "es obligatorio en acciones de tipo clasificar"
        )
    if tipo == "renombrar":
        plantilla = accion["plantilla"]
        if not isinstance(plantilla, str):
            raise AccionNoValida(nombre, "plantilla", "debe ser un texto")
        prueba = datetime(2026, 1, 2, 3, 4)
        try:
            plantilla.format(fecha=prueba, n=1, ext=".jpg", nombre="fichero")
        except (KeyError, IndexError, ValueError) as e:
            raise AccionNoValida(
                nombre,
                "plantilla",
                f"hueco inválido: {e}; los huecos válidos son «fecha», «n», «ext» y «nombre»",
            ) from e
    if tipo == "borrar" and "confirmar" in accion and not isinstance(
        accion["confirmar"], bool
    ):
        raise AccionNoValida(nombre, "confirmar", "debe ser true o false")
    if tipo in TIPOS_IA:
        validar_ia(nombre, accion)
    _validar_filtro(accion, nombre)


def cargar(ruta: Path) -> list[dict]:
    """Lee acciones.json y devuelve la lista de acciones validadas."""
    ruta = ruta.expanduser()
    if not ruta.is_file():
        raise ConfigError(f"No encuentro {ruta}. Crea acciones.json o usa --config RUTA")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"{ruta.name} no es JSON válido: línea {e.lineno}, columna {e.colno} ({e.msg})"
        ) from e
    if not isinstance(datos, dict):
        raise ConfigError("La raíz de acciones.json debe ser un objeto")
    if datos.get("version") != 1:
        raise ConfigError(
            f"Versión del esquema «{datos.get('version')}» no soportada; la actual es 1"
        )
    acciones = datos.get("acciones")
    if not isinstance(acciones, list) or not acciones:
        raise ConfigError("Falta la lista «acciones» o está vacía")
    vistos: set[str] = set()
    for accion in acciones:
        _validar_accion(accion, vistos)
    return acciones
