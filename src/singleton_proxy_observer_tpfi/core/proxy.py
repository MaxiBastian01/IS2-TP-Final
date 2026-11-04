from core.singleton import DynamoDBSingleton


class CorporateDataProxy:

    def __init__(self):
        self.db = DynamoDBSingleton()

    
    def guardar_registro(self, datos):
        if not datos.get("ID"):
            raise ValueError("Falta el ID del registro")

        id_registro = datos["ID"]

        campos = [
            "cp", "CUIT", "domicilio", "idreq",
            "idSeq", "localidad", "provincia",
            "sede", "seqID", "telefono", "web"
        ]

        registro = self.db.obtener_registro(id_registro)

        if registro is None:
            registro = {"id": id_registro}
            for campo in campos:
                registro[campo] = ""

        for campo in campos:
            if campo in datos:
                registro[campo] = datos[campo]

        return self.db.guardar_registro(registro)
