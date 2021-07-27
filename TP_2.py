from genericpath import getsize
import os
import service_drive
import service_gmail
import io
import hashlib
from datetime import datetime
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

EXTENSIONES_VALIDAS = ["txt", "jpg", "mp3", "mp4", "pdf"]  # Se pueden agregar mas


def clear() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def crear_carpeta_remota(nombre: str, idCarpeta: str) -> str:
    metaCarpeta = {
        "name": f"{nombre}",
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [idCarpeta],
    }
    carpeta = (
        service_drive.obtener_servicio()
        .files()
        .create(body=metaCarpeta, fields="id")
        .execute()
    )
    return carpeta.get("id")  # Quiza es mejor retornar toda la respuesta


def root_drive() -> str:  # Esta funcion crea una carpeta tipo root para todos los archivos del trabajo
    query = "mimeType = 'application/vnd.google-apps.folder' and parents = 'root'"
    field = "files(id, name)"
    respuesta = (
        service_drive.obtener_servicio().files().list(q=query, fields=field).execute()
    )
    for carpeta in respuesta.get("files"):
        if carpeta.get("name") == "TP_2Algo15":
            return carpeta.get("id")
    return crear_carpeta_remota("TP_2Algo15", "root")


def root_local() -> str:  # Similar para local
    path = os.getcwd()
    directorio = os.listdir(path)
    for archivo in directorio:
        if archivo == "TP_2Algo15" and os.path.isdir(os.path.join(path, archivo)):
            return os.path.join(path, archivo)
    path = os.path.join(path, "TP_2Algo15")
    os.mkdir(path)
    return path


ROOT_DRIVE = (
    root_drive()
)  # Variable global porque no tendria sentido salirse de esta carpeta

ROOT_LOCAL = root_local()  # Similar a ROOT_DRIVE


def ver_archivos(path: str) -> None:  # Esta parte puede servir para otras funciones.
    directorio = os.listdir(path)
    for archivo in directorio:
        print(archivo)


def ver_archivos_remoto(idCarpeta: str) -> dict:  # Similar
    query = f"parents = '{idCarpeta}'"
    field = "files(id, name, mimeType)"
    respuesta = (
        service_drive.obtener_servicio().files().list(q=query, fields=field).execute()
    )
    for archivo in respuesta.get("files"):
        print(archivo.get("name"))
    return respuesta


def anidar_carpetas_remoto(
    path: str,
) -> str:  # Crea carpetas automaticamente si no existen en Drive
    anidacion = []
    while not os.path.split(path)[1] == os.path.split(ROOT_LOCAL)[1]:
        anidacion.insert(0, os.path.split(path)[1])
        path = os.path.split(path)[0]

    idCarpeta = ROOT_DRIVE
    while not anidacion == []:
        query = f"mimeType = 'application/vnd.google-apps.folder' and parents = '{idCarpeta}'"
        field = "files(id, name)"
        respuesta = (
            service_drive.obtener_servicio()
            .files()
            .list(q=query, fields=field)
            .execute()
        )

        idCarpetaAux = str()  # Variable auxiliar
        for carpeta in respuesta.get("files"):
            if carpeta.get("name") == anidacion[0]:
                idCarpetaAux = carpeta.get("id")

        if idCarpetaAux != "":
            idCarpeta = idCarpetaAux
            anidacion.pop(0)
        else:
            idCarpeta = crear_carpeta_remota(anidacion[0], idCarpeta)
            anidacion.pop(0)

    return idCarpeta


def subir_archivo(
    path: str, nombre, idCarpeta: str
) -> None:  # ¿Deberia comparar archivos aca?
    if os.path.isdir(path):
        directorio = os.listdir(path)
        idCarpetaAux = anidar_carpetas_remoto(path)  # idCarpetaAux variable auxiliar.
        for archivo in directorio:
            subir_archivo(os.path.join(path, archivo), archivo, idCarpetaAux)

    else:
        meta_archivo = {"name": nombre, "parents": [idCarpeta]}

        media = MediaFileUpload(path)
        service_drive.obtener_servicio().files().create(
            body=meta_archivo, media_body=media, fields="id"
        ).execute()


def descargar_archivo(
    idArchivo: str, tipo: str, nombre: str, path: str
) -> None:  # ¿Deberia comparar aca?
    if tipo == "application/vnd.google-apps.folder":
        if not os.path.isdir(os.path.join(path, nombre)):
            os.mkdir(os.path.join(path, nombre))

        query = f"parents = '{idArchivo}'"
        field = "files(id, name, mimeType)"
        respuesta = (
            service_drive.obtener_servicio()
            .files()
            .list(q=query, fields=field)
            .execute()
        )
        for archivo in respuesta.get("files"):
            descargar_archivo(
                archivo.get("id"),
                archivo.get("mimeType"),
                archivo.get("name"),
                os.path.join(path, nombre),
            )

    else:
        bytes = io.BytesIO()
        respuesta = service_drive.obtener_servicio().files().get_media(fileId=idArchivo)
        descarga = MediaIoBaseDownload(bytes, respuesta)

        completo = False
        while not completo:
            _, completo = descarga.next_chunk()
        bytes.seek(0)

        with open(os.path.join(path, nombre), "wb") as archivo:
            archivo.write(bytes.read())


def navegador_local():  # ESTA ES LA PRINCIPAL PARA LOCAL
    selector = str()
    path = ROOT_LOCAL
    while not selector == "4":
        clear()
        ver_archivos(path)
        selector = input(  # Esto se podria mejorar para que sea mas intuitivo
            """
        Ingrese la carpeta a la que quiera ingresar,
        1: Volver al directorio anterior,
        2: Crear un archivo en este directorio,
        3: Subir un archivo,
        4: Volver al menu principal: """
        )

        if selector == "1":
            if not path == ROOT_LOCAL:
                path = os.path.dirname(path)

        elif selector == "2":
            opcion = input(
                "\nIngrese 1 para crear una carpeta, 2 para crear un archivo: "
            )
            if opcion == "1":
                nombre = input(
                    "Ingrese el nombre de la carpeta: "
                )  # ¿Que pasa si agrego extension?
                os.mkdir(os.path.join(path, nombre))
                idCarpeta = anidar_carpetas_remoto(path)
                crear_carpeta_remota(nombre, idCarpeta)

            if opcion == "2":
                nombre = input(
                    "Ingrese el nombre del archivo: "
                )  # ¿Que pasa si agrego extension?

                print("Extensiones validas:")
                for extension in range(len(EXTENSIONES_VALIDAS)):
                    print(EXTENSIONES_VALIDAS[extension])
                extension = input("Ingrese la extension del archivo: ")

                while not extension in EXTENSIONES_VALIDAS:
                    extension = input("Ingrese una extension valida: ")

                pathArchivo = f"{os.path.join(path,nombre)}.{extension}"
                nombreExtension = f"{nombre}.{extension}"

                with open(pathArchivo, "w") as _:
                    pass

                idCarpeta = anidar_carpetas_remoto(path)
                subir_archivo(pathArchivo, nombreExtension, idCarpeta)

        elif selector == "3":
            nombre = input("\nIngrese el nombre del archivo o carpeta a subir: ")
            while not (
                os.path.isdir(os.path.join(path, nombre))
                or os.path.isfile(os.path.join(path, nombre))
            ):
                nombre = input("Ingrese un archivo valido: ")

            idCarpeta = ROOT_DRIVE
            opcion = str()
            while not opcion == "1":  # Aca se repite codigo
                clear()
                respuesta = ver_archivos_remoto(idCarpeta)
                opcion = input(
                    """
                Ingrese la carpeta a la que quiera ingresar,
                1 para subir,
                2 para volver al directorio principal: """
                )
                if opcion == "2":
                    idCarpeta = ROOT_DRIVE
                else:
                    for archivo in respuesta.get("files"):
                        if (
                            archivo.get("name") == opcion
                            and archivo.get("mimeType")
                            == "application/vnd.google-apps.folder"
                        ):
                            idCarpeta = archivo.get("id")

            subir_archivo(os.path.join(path, nombre), nombre, idCarpeta)

        else:
            if os.path.isdir(os.path.join(path, selector)):
                path = os.path.join(path, selector)


def navegador_remoto() -> None:  # ESTA ES LA PRINCIPAL PARA REMOTO
    idCarpeta = ROOT_DRIVE
    selector = str()
    while not selector == "3":
        clear()
        respuesta = ver_archivos_remoto(idCarpeta)
        selector = input(
            """
        Ingrese la carpeta a la que quiera ingresar,
        1 Volver al directorio principal,
        2 Descargar un archivo,
        3 Volver al menu principal: """
        )

        if selector == "1":
            idCarpeta = ROOT_DRIVE

        elif selector == "2":
            condicion = False
            while not condicion:
                nombre = input(
                    "\nIngrese el nombre del archivo o carpeta a descargar: "
                )
                for archivo in respuesta.get("files"):
                    if nombre == archivo.get("name"):
                        idArchivo = archivo.get("id")
                        tipo = archivo.get("mimeType")
                        condicion = True

            path = ROOT_LOCAL
            opcion = str()
            while not opcion == "1":  # Aca se repite codigo
                clear()
                ver_archivos(path)
                opcion = input(
                    """
                    Ingrese la carpeta a la que quiera ingresar,
                    1 para descargar,
                    2 para volver al directorio anterior: """
                )
                if opcion == "2":
                    if not path == ROOT_LOCAL:
                        path = os.path.dirname(path)

                if os.path.isdir(os.path.join(path, opcion)):
                    path = os.path.join(path, opcion)

            descargar_archivo(idArchivo, tipo, nombre, path)

        else:
            for archivo in respuesta.get("files"):
                if (
                    archivo.get("name") == selector
                    and archivo.get("mimeType") == "application/vnd.google-apps.folder"
                ):
                    idCarpeta = archivo.get("id")


def sincronizar(idCarpeta: str, path: str) -> None:
    query = f"parents = '{idCarpeta}'"
    field = "files(id, name, mimeType, modifiedTime, md5Checksum)"
    respuesta = (
        service_drive.obtener_servicio().files().list(q=query, fields=field).execute()
    )
    directorio = os.listdir(path)
    directorioRemoto = []
    for archivo in respuesta.get("files"):
        directorioRemoto.append(archivo.get("name"))

    for archivo in respuesta.get("files"):
        pathArchivo = os.path.join(path, archivo.get("name"))
        if (
            archivo.get("mimeType") == "application/vnd.google-apps.folder"
            and archivo.get("name") in directorio
        ):
            sincronizar(archivo.get("id"), pathArchivo)
        if (
            archivo.get("name") in directorio
            and not archivo.get("mimeType") == "application/vnd.google-apps.folder"
        ):
            checksumLocal = hashlib.md5(open(f"{pathArchivo}", "rb").read()).hexdigest()
            checksumRemoto = archivo.get("md5Checksum")
            if checksumLocal != checksumRemoto:
                mtimeLocal = datetime.utcfromtimestamp(os.path.getmtime(pathArchivo))
                mtimeRemoto = datetime.strptime(
                    archivo.get("modifiedTime"), "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                if mtimeRemoto > mtimeLocal:
                    descargar_archivo(
                        archivo.get("id"),
                        archivo.get("mimeType"),
                        archivo.get("name"),
                        path,
                    )
                else:
                    service_drive.obtener_servicio().files().delete(
                        fileId=archivo.get("id")
                    ).execute()
                    subir_archivo(pathArchivo, archivo.get("name"), idCarpeta)
        else:
            descargar_archivo(
                archivo.get("id"),
                archivo.get("mimeType"),
                archivo.get("name"),
                path,
            )

    for archivo in directorio:
        if not archivo in directorioRemoto:
            subir_archivo(os.path.join(path, archivo), archivo, idCarpeta)


def main() -> None:
    selector = str()
    while not selector == "8":
        clear()
        print(
            """
        1. Listar archivos de la carpeta actual
        2. Crear un archivo
        3. Subir un archivo
        4. Descargar un archivo
        5. Sincronizar.
        6. Generar carpetas de una evaluacion
        7. Actualizar entregas de alumnos via mail
        8. Salir"""
        )
        selector = input("\nIngrese una opcion: ")

        if selector == "1":
            opcion = input("Ingrese 1 para Local, 2 para Remoto: ")
            if opcion == "1":
                navegador_local()
            if opcion == "2":
                navegador_remoto()

        elif selector == "2":
            navegador_local()

        elif selector == "3":
            navegador_local()

        elif selector == "4":
            navegador_remoto()

        elif selector == "5":
            sincronizar(ROOT_DRIVE, ROOT_LOCAL)

        elif selector == "6":
            pass

        elif selector == "7":
            pass


main()
