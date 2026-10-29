# src/tareas/errores.py
"""Excepciones propias de la herramienta: cada una trae su código de salida."""


class TareasError(Exception):
    """Base de todos los errores previsibles de la herramienta."""

    codigo_salida = 1


class ConfigError(TareasError):
    """acciones.json no existe, no es JSON o no cumple el esquema."""

    codigo_salida = 3


class AccionNoValida(ConfigError):
    """Una acción concreta tiene un campo mal: dice cuál y por qué."""

    def __init__(self, accion: str, campo: str, motivo: str):
        super().__init__(f"Acción «{accion}», campo «{campo}»: {motivo}")
        self.accion = accion
        self.campo = campo
