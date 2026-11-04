import sys
from pathlib import Path
from unittest.mock import MagicMock

ruta = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "singleton_proxy_observer_tpfi"
)

sys.path.insert(0, str(ruta))

from core.proxy import CorporateDataProxy


def test_proxy_modificacion_parcial():
    proxy = CorporateDataProxy()

    # Simulamos DynamoDB para no modificar datos reales
    proxy.db = MagicMock()

    proxy.db.obtener_registro.return_value = {
        "id": "asd-IS2",
        "localidad": "Concepción del Uruguay",
        "sede": "Original"
    }

    datos = {
        "ID": "asd-IS2",
        "sede": "Actualizada"
    }

    proxy.guardar_registro(datos)

    registro_guardado = proxy.db.guardar_registro.call_args.args[0]

    assert registro_guardado["sede"] == "Actualizada"
    assert registro_guardado["localidad"] == "Concepción del Uruguay"