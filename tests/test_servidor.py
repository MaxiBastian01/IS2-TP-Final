
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

RUTA = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "singleton_proxy_observer_tpfi"
)

sys.path.insert(0, str(RUTA))

# El servidor utiliza argparse al importarse.
# Evitamos que lea los argumentos de pytest.
argumentos_originales = sys.argv[:]

try:
    sys.argv = ["singletonproxyobservertpfi.py"]
    servidor = importlib.import_module("singletonproxyobservertpfi")
finally:
    sys.argv = argumentos_originales


@pytest.fixture
def dependencias(monkeypatch):
    db = MagicMock()
    proxy = MagicMock()
    observer = MagicMock()
    log_db = MagicMock()

    monkeypatch.setattr(servidor, "db", db)
    monkeypatch.setattr(servidor, "proxy", proxy)
    monkeypatch.setattr(servidor, "observer", observer)
    monkeypatch.setattr(servidor, "log_db", log_db)

    return db, proxy, observer, log_db


def enviar_solicitud(datos):
    conexion = MagicMock()
    conexion.recv.return_value = json.dumps(datos).encode("utf-8")

    servidor.atender_cliente(conexion, ("localhost", 12345))

    conexion.close.assert_called_once()

    respuesta = json.loads(
        conexion.sendall.call_args.args[0].decode("utf-8")
    )

    return respuesta


def test_servidor_get(dependencias):
    db, _proxy, _observer, log_db = dependencias

    db.obtener_registro.return_value = {
        "id": "TEST",
        "sede": "UADER"
    }

    respuesta = enviar_solicitud({
        "UUID": "123456",
        "ACTION": "get",
        "ID": "TEST"
    })

    assert respuesta["ACTION"] == "get"
    assert respuesta["DATA"]["sede"] == "UADER"

    db.obtener_registro.assert_called_once_with("TEST")

    log = log_db.guardar_log.call_args.args[0]
    assert log["ACTION"] == "get"
    assert log["ID"] == "TEST"
    assert log["UUID"] == "123456"


def test_servidor_list(dependencias):
    db, _proxy, _observer, log_db = dependencias

    db.listar_registros.return_value = [
        {"id": "1"},
        {"id": "2"}
    ]

    respuesta = enviar_solicitud({
        "UUID": "123456",
        "ACTION": "list"
    })

    assert respuesta["ACTION"] == "list"
    assert len(respuesta["DATA"]) == 2

    db.listar_registros.assert_called_once()

    log = log_db.guardar_log.call_args.args[0]
    assert log["ACTION"] == "list"


def test_servidor_set(dependencias):
    _db, proxy, observer, log_db = dependencias

    proxy.guardar_registro.return_value = {
        "id": "TEST",
        "sede": "UADER"
    }

    respuesta = enviar_solicitud({
        "UUID": "123456",
        "ACTION": "set",
        "ID": "TEST",
        "sede": "UADER"
    })

    assert respuesta["ACTION"] == "set"
    assert respuesta["DATA"]["sede"] == "UADER"

    observer.notificar.assert_called_once_with(
        "TEST",
        {"id": "TEST", "sede": "UADER"}
    )

    log = log_db.guardar_log.call_args.args[0]
    assert log["ACTION"] == "set"



def test_servidor_subscribe(dependencias):
    _db, _proxy, observer, log_db = dependencias

    conexion = MagicMock()

    conexion.recv.side_effect = [
        json.dumps({
            "UUID": "123456",
            "ACTION": "subscribe"
        }).encode("utf-8"),
        b""
    ]

    servidor.atender_cliente(
        conexion,
        ("localhost", 12345)
    )

    observer.suscribir.assert_called_once_with(
        "123456",
        conexion
    )

    log = log_db.guardar_log.call_args.args[0]

    assert log["ACTION"] == "subscribe"
    assert log["UUID"] == "123456"

    conexion.close.assert_called_once()


def test_servidor_sin_action(dependencias):
    conexion = MagicMock()
    conexion.recv.return_value = json.dumps({
        "UUID": "123456"
    }).encode("utf-8")

    with pytest.raises(KeyError):
        servidor.atender_cliente(
            conexion,
            ("localhost", 12345)
        )

    conexion.close.assert_called_once()


def test_servidor_get_sin_id(dependencias):
    conexion = MagicMock()
    conexion.recv.return_value = json.dumps({
        "UUID": "123456",
        "ACTION": "get"
    }).encode("utf-8")

    with pytest.raises(KeyError):
        servidor.atender_cliente(
            conexion,
            ("localhost", 12345)
        )

    conexion.close.assert_called_once()


def test_iniciar_servidor(monkeypatch):
    import importlib.util
    import sys
    from pathlib import Path
    from unittest.mock import MagicMock

    ruta = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "singleton_proxy_observer_tpfi"
        / "singletonproxyobservertpfi.py"
    )

    spec = importlib.util.spec_from_file_location(
        "servidor_test_inicio", ruta
    )
    servidor_inicio = importlib.util.module_from_spec(spec)

    argumentos_originales = sys.argv[:]

    try:
        sys.argv = [str(ruta)]
        spec.loader.exec_module(servidor_inicio)
    finally:
        sys.argv = argumentos_originales

    # Simular dependencias de AWS
    monkeypatch.setattr(servidor_inicio, "DynamoDBSingleton", MagicMock())
    monkeypatch.setattr(servidor_inicio, "CorporateDataProxy", MagicMock())
    monkeypatch.setattr(servidor_inicio, "CorporateDataObserver", MagicMock())
    monkeypatch.setattr(servidor_inicio, "CorporateLogSingleton", MagicMock())

    # Simular socket TCP
    socket_falso = MagicMock()
    socket_falso.accept.side_effect = OSError("Fin de prueba")

    monkeypatch.setattr(
        servidor_inicio.socket,
        "socket",
        MagicMock(return_value=socket_falso)
    )

    with pytest.raises(OSError, match="Fin de prueba"):
        servidor_inicio.iniciar_servidor()

    socket_falso.bind.assert_called_once_with(
        (servidor_inicio.HOST, servidor_inicio.PORT)
    )
    socket_falso.listen.assert_called_once()
    socket_falso.close.assert_called_once()