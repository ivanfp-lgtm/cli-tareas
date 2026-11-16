# tests/test_cli.py: la CLI desde fuera, una prueba por código de salida
from typer.testing import CliRunner

from tareas.cli import app

runner = CliRunner()


def test_la_ayuda_funciona():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "tareas" in r.output


def test_json_roto_sale_con_3_y_sin_traza(escribir_config):
    r = runner.invoke(
        app, ["--config", str(escribir_config('{"version": 1, "acciones": [ } ]')), "validar"]
    )
    assert r.exit_code == 3
    assert "no es JSON válido" in r.output
    assert "Traceback" not in r.output


def test_accion_que_no_existe_sale_con_1(escribir_config, descargas):
    ruta = escribir_config([{"nombre": "a", "descripcion": "x", "tipo": "borrar"}])
    r = runner.invoke(app, ["--config", str(ruta), "ejecutar", "inventada", str(descargas)])
    assert r.exit_code == 1


def test_opcion_que_no_existe_sale_con_2():
    r = runner.invoke(app, ["listar", "--inventada"])
    assert r.exit_code == 2


def test_ia_sin_clave_sale_con_4_y_avisa(escribir_config, descargas):
    ruta = escribir_config(
        [{"nombre": "res", "descripcion": "x", "tipo": "resumir"}]
    )
    r = runner.invoke(app, ["--config", str(ruta), "ejecutar", "res", str(descargas)])
    assert r.exit_code == 4
    assert "siguen funcionando" in r.output
