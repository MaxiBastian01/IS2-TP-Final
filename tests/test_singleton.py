import sys
from pathlib import Path

ruta = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "singleton_proxy_observer_tpfi"
)

sys.path.insert(0, str(ruta))

from core.singleton import DynamoDBSingleton


def test_singleton_misma_instancia():
    instancia1 = DynamoDBSingleton()
    instancia2 = DynamoDBSingleton()

    assert instancia1 is instancia2