# tests/test_acciones.py: las acciones con ficheros reales, pero en tmp_path
import pytest

from tareas.errores import TareasError
from tareas.motor import Motor


def motor_con(**accion) -> Motor:
    return Motor([{"nombre": "prueba", "descripcion": "acción de prueba", **accion}])


def test_mover_solo_lo_que_cumple_el_filtro(descargas, tmp_path):
    destino = tmp_path / "PDF"
    motor = motor_con(
        tipo="mover", filtro={"extensiones": [".pdf", ".docx"]}, destino=str(destino)
    )
    resultados = motor.ejecutar("prueba", descargas, simular=False)
    assert sorted(f.name for f in destino.iterdir()) == [
        "apuntes de redes.docx",
        "factura.pdf",
    ]
    assert [r.estado for r in resultados] == ["hecho", "hecho"]
    assert (descargas / "FOTO1.JPG").exists()


def test_simular_no_toca_el_disco(descargas, tmp_path):
    destino = tmp_path / "PDF"
    antes = sorted(descargas.iterdir())
    motor = motor_con(
        tipo="mover", filtro={"extensiones": [".pdf"]}, destino=str(destino)
    )
    motor.ejecutar("prueba", descargas, simular=True)
    assert sorted(descargas.iterdir()) == antes
    assert not destino.exists()  # ni siquiera un mkdir


def test_nunca_sobrescribe(descargas, tmp_path):
    destino = tmp_path / "PDF"
    destino.mkdir()
    (destino / "factura.pdf").write_text("la que ya estaba", encoding="utf-8")
    motor_con(
        tipo="mover", filtro={"extensiones": [".pdf"]}, destino=str(destino)
    ).ejecutar("prueba", descargas, False)
    vieja, nueva = destino / "factura.pdf", destino / "factura (1).pdf"
    assert vieja.read_text(encoding="utf-8") == "la que ya estaba"
    assert nueva.exists()


def test_la_extension_en_mayusculas_cuenta(descargas):
    elegidos = Motor.seleccionar(descargas, {"extensiones": [".jpg"]})
    assert [f.name for f in elegidos] == ["FOTO1.JPG"]


def test_borrar_solo_los_viejos(descargas):
    (descargas / "nuevo.tmp").write_text("", encoding="utf-8")
    filtro = {"patron": r"\.tmp$", "mas_antiguo_que_dias": 30}
    motor_con(tipo="borrar", filtro=filtro).ejecutar("prueba", descargas, simular=False)
    assert not (descargas / "viejo.tmp").exists()
    assert (descargas / "nuevo.tmp").exists()


def test_renombrar_con_plantilla(descargas):
    motor = motor_con(
        tipo="renombrar",
        filtro={"extensiones": [".jpg", ".png"]},
        plantilla="foto-{n:03}{ext}",
    )
    resultados = motor.ejecutar("prueba", descargas, simular=False)
    assert (descargas / "foto-001.jpg").exists()
    assert (descargas / "foto-002.png").exists()
    # «FOTO1.JPG» → foto-001.jpg y «cumpleaños 2.png» → foto-002.png: son
    # nombres BASE distintos, así que en cualquier SO caben los dos y no
    # puede salir el sufijo « (1)».
    assert not (descargas / "foto-001 (1).jpg").exists()
    assert not (descargas / "foto-002 (1).png").exists()


def test_mismo_nombre_solo_mayusculas_no_achasta(descargas):
    # «FOTO1.JPG» → «FOTO1-nuevo.JPG»: el nombre base cambia, así que en
    # cualquier SO (distinga o no mayúsculas) se renombra. Lo que NO puede
    # pasar es que acabe en « (1)», que era el bug del casefold en
    # destino_libre.
    motor = motor_con(
        tipo="renombrar",
        filtro={"patron_nombre": "^FOTO1$"},
        plantilla="{nombre}-nuevo{ext}",
    )
    resultados = motor.ejecutar("prueba", descargas, simular=False)
    r = resultados[0]
    assert r.estado == "hecho"
    assert r.destino.name == "FOTO1-nuevo.jpg"  # la extensión, siempre en minúsculas
    assert (descargas / "FOTO1-nuevo.jpg").exists()
    assert not (descargas / "FOTO1.JPG").exists()


def test_cambio_de_mayusculas_es_un_rename_normal(descargas):
    # «FOTO1.JPG» → «foto1.JPG»: en Windows/macOS(%) es EL MISMO fichero y
    # se marca «saltado»; en Linux se renombra de verdad. En ningún caso a
    # « (1)».
    from tareas.acciones import el_so_no_distingue_mayusculas

    caso = el_so_no_distingue_mayusculas(descargas)
    motor = motor_con(
        tipo="renombrar",
        filtro={"patron_nombre": "^FOTO1$"},
        plantilla="foto1.jpg",  # mismo nombre y misma extensión: un rename de mayúsculas
    )
    resultados = motor.ejecutar("prueba", descargas, simular=False)
    r = resultados[0]
    if caso:
        # El SO ve «foto1.jpg» ocupado por «FOTO1.JPG»: se marca «saltado»
        # y el fichero no se toca. Es la ÚNICA forma segura, porque un
        # rename con el nombre que solo difiere en mayúsculas PETA en
        # Windows (lo probamos en Actions).
        assert r.estado == "saltado"
        assert (descargas / "FOTO1.JPG").exists()
    else:
        assert r.estado == "hecho"
        assert (descargas / "foto1.jpg").exists()
        assert not (descargas / "FOTO1.JPG").exists()
    assert " (1)" not in (r.destino.name if r.destino else "")


def test_la_accion_inexistente_da_error_claro(descargas):
    motor = motor_con(tipo="borrar")
    with pytest.raises(TareasError, match="tareas acciones"):
        motor.ejecutar("no-existe", descargas, simular=True)
