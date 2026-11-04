"""Pruebas unitarias del TP Final IS2 (sin escrituras reales en AWS)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT = Path(__file__).resolve().parents[1] / 'src' / 'singleton_proxy_observer_tpfi'
sys.path.insert(0, str(PROJECT))

from core.log_singleton import CorporateLogSingleton
from core.observer import CorporateDataObserver
from core.proxy import CorporateDataProxy
from core.singleton import DynamoDBSingleton


def test_singleton_misma_instancia():
    assert DynamoDBSingleton() is DynamoDBSingleton()


def test_log_singleton_misma_instancia():
    assert CorporateLogSingleton() is CorporateLogSingleton()


def test_singleton_obtener_registro():
    db = DynamoDBSingleton()
    tabla = MagicMock()
    tabla.get_item.return_value = {'Item': {'id': 'prueba'}}
    with patch.object(db.dynamodb, 'Table', return_value=tabla):
        assert db.obtener_registro('prueba') == {'id': 'prueba'}
        tabla.get_item.assert_called_once_with(Key={'id': 'prueba'})


def test_singleton_obtener_inexistente():
    db = DynamoDBSingleton()
    tabla = MagicMock()
    tabla.get_item.return_value = {}
    with patch.object(db.dynamodb, 'Table', return_value=tabla):
        assert db.obtener_registro('no-existe') is None


def test_singleton_listar_paginado():
    db = DynamoDBSingleton()
    tabla = MagicMock()
    tabla.scan.side_effect = [
        {'Items': [{'id': 'a'}], 'LastEvaluatedKey': {'id': 'a'}},
        {'Items': [{'id': 'b'}]},
    ]
    with patch.object(db.dynamodb, 'Table', return_value=tabla):
        assert db.listar_registros() == [{'id': 'a'}, {'id': 'b'}]
        assert tabla.scan.call_count == 2


def test_singleton_guardar():
    db = DynamoDBSingleton()
    tabla = MagicMock()
    with patch.object(db.dynamodb, 'Table', return_value=tabla):
        assert db.guardar_registro({'id': 'x'}) == {'id': 'x'}
        tabla.put_item.assert_called_once_with(Item={'id': 'x'})


def test_log_guardar():
    db = CorporateLogSingleton()
    tabla = MagicMock()
    with patch.object(db.dynamodb, 'Table', return_value=tabla):
        assert db.guardar_log({'id': 'log-1'}) == {'id': 'log-1'}
        tabla.put_item.assert_called_once_with(Item={'id': 'log-1'})


def test_proxy_set_parcial():
    proxy = CorporateDataProxy()
    proxy.db = MagicMock()
    proxy.db.obtener_registro.return_value = {'id': 'x', 'localidad': 'Concepcion', 'sede': 'Vieja'}
    proxy.guardar_registro({'ID': 'x', 'sede': 'Nueva'})
    guardado = proxy.db.guardar_registro.call_args.args[0]
    assert guardado['sede'] == 'Nueva'
    assert guardado['localidad'] == 'Concepcion'


def test_proxy_set_nuevo():
    proxy = CorporateDataProxy()
    proxy.db = MagicMock()
    proxy.db.obtener_registro.return_value = None
    proxy.guardar_registro({'ID': 'nuevo', 'sede': 'FCyT'})
    guardado = proxy.db.guardar_registro.call_args.args[0]
    assert guardado['id'] == 'nuevo'
    assert guardado['sede'] == 'FCyT'
    assert guardado['telefono'] == ''


def test_proxy_sin_id():
    proxy = CorporateDataProxy()
    with pytest.raises(ValueError, match='ID'):
        proxy.guardar_registro({'sede': 'FCyT'})


def test_observer_suscribir_y_notificar():
    observer = CorporateDataObserver()
    conexion = MagicMock()
    observer.suscribir('uuid-1', conexion)
    observer.notificar('x', {'id': 'x', 'sede': 'FCyT'})
    import json
    mensaje = json.loads(conexion.sendall.call_args.args[0].decode('utf-8'))
    assert mensaje['ACTION'] == 'notification'
    assert mensaje['DATA']['id'] == 'x'


def test_observer_notifica_a_dos():
    observer = CorporateDataObserver()
    c1, c2 = MagicMock(), MagicMock()
    observer.suscribir('uuid-1', c1)
    observer.suscribir('uuid-2', c2)
    observer.notificar('x', {'id': 'x'})
    c1.sendall.assert_called_once()
    c2.sendall.assert_called_once()


def test_observer_elimina_desconectado():
    observer = CorporateDataObserver()
    conexion = MagicMock()
    conexion.sendall.side_effect = OSError('desconectado')
    observer.suscribir('uuid-1', conexion)
    observer.notificar('x', {'id': 'x'})
    assert 'uuid-1' not in observer.suscriptores
