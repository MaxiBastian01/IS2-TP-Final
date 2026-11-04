import json


class CorporateDataObserver:
    def __init__(self):
        self.suscriptores = {}

    def suscribir(self, uuid_cliente, conexion):
        self.suscriptores[uuid_cliente] = conexion

    def notificar(self, id_registro, registro):
        mensaje = {
            "ACTION": "notification",
            "DATA": registro
        }

        mensaje_json = json.dumps(mensaje, default=str)

        for uuid_cliente, conexion in list(self.suscriptores.items()):
            try:
                conexion.sendall(mensaje_json.encode("utf-8"))
            except OSError:
                del self.suscriptores[uuid_cliente]