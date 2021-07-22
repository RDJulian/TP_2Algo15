import os
import service_drive
import service_gmail
import io
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
    idArchivo: str, type: str, nombre: str, path: str
) -> None:  # ¿Deberia comparar aca?
    if type == "application/vnd.google-apps.folder":
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
            estado, completo = descarga.next_chunk()
            print(f"Descarga del archivo: {estado.progress() * 100}%")
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
                nombre = input("Ingrese el nombre de la carpeta: ")
                os.mkdir(os.path.join(path, nombre))
                idCarpeta = anidar_carpetas_remoto(path)
                crear_carpeta_remota(nombre, idCarpeta)

            if opcion == "2":
                nombre = input("Ingrese el nombre del archivo: ")

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
            pass

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
            pass

        else:
            for archivo in respuesta.get("files"):
                if (
                    archivo.get("name") == selector
                    and archivo.get("mimeType") == "application/vnd.google-apps.folder"
                ):
                    idCarpeta = archivo.get("id")


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
            pass

        elif selector == "4":
            pass

        elif selector == "5":
            pass

        elif selector == "6":
            pass

        elif selector == "7":
            pass


main()
