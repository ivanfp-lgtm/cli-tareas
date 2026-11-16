# tests/test_config.py: acciones.json se valida ANTES de tocar nada
import pytest

from tareas import config
from tareas.errores import AccionNoValida, ConfigError

BUENA = {"nombre": "ordenar", "descripcion": "Mueve los PDF", "tipo": "mover", "destino": "~/PDF"}


def test_una_config_buena_se_carga(escribir_config):
    acciones = config.cargar(escribir_config([BUENA]))
    assert [a["nombre"] for a in acciones] == ["ordenar"]


@pytest.mark.parametrize(
    "cambio, campo",
    [
        ({"tipo": "mober"}, "tipo"),
        ({"destino": ""}, "destino"),
        ({"descripcion": None}, "descripcion"),
        ({"filtro": {"patron": "*.tmp"}}, "filtro.patron"),
    ],
    ids=["tipo-inexistente", "destino-vacio", "sin-descripcion", "regex-rota"],
)
def test_el_error_dice_que_campo_falla(escribir_config, cambio, campo):
    with pytest.raises(AccionNoValida) as error:
        config.cargar(escribir_config([BUENA | cambio]))
    assert error.value.campo == campo


def test_nombre_repetido(escribir_config):
    with pytest.raises(AccionNoValida, match="está repetido"):
        config.cargar(escribir_config([BUENA, BUENA]))


def test_json_roto_dice_la_linea(escribir_config):
    with pytest.raises(ConfigError, match="línea 1"):
        config.cargar(escribir_config('{"version": 1, "acciones": [ } ]'))


def test_fichero_que_no_existe(tmp_path):
    with pytest.raises(ConfigError, match="No encuentro"):
        config.cargar(tmp_path / "nada.json")


def test_campos_de_IA_validan_bien(escribir_config):
    accion = {
        "nombre": "res",
        "descripcion": "Resume",
        "tipo": "resumir",
        "instrucciones": "Resume en 5 viñetas",
        "max_caracteres": 8000,
    }
    acciones = config.cargar(escribir_config([accion]))
    assert acciones[0]["tipo"] == "resumir"


@pytest.mark.parametrize(
    "cambio, campo",
    [
        ({"max_caracteres": 10}, "max_caracteres"),
        ({"max_caracteres": 999999}, "max_caracteres"),
        ({"instrucciones": 5}, "instrucciones"),
        ({"categorias": []}, "categorias"),
    ],
    ids=["tope-corto", "tope-largo", "instrucciones-numero", "categorias-vacias"],
)
def test_los_campos_de_IA_feos_fallan(escribir_config, cambio, campo):
    accion = {"nombre": "res", "descripcion": "Resume", "tipo": "resumir"} | cambio
    with pytest.raises(AccionNoValida) as error:
        config.cargar(escribir_config([accion]))
    assert error.value.campo == campo


def test_clasificar_pide_categorias_y_destino(escribir_config):
    accion = {"nombre": "cla", "descripcion": "x", "tipo": "clasificar"}
    with pytest.raises(AccionNoValida) as error:
        config.cargar(escribir_config([accion]))
    assert error.value.campo == "categorias"
