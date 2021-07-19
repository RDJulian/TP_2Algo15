import os
import service_drive
import service_gmail


def clear() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def root_drive() -> str:  # Esta funcion crea una carpeta tipo root para todos los archivos del trabajo
    query = "mimeType = 'application/vnd.google-apps.folder' and parents = 'root'"
    field = "files(id, name)"
    respuesta = (
        service_drive.obtener_servicio().files().list(q=query, fields=field).execute()
    )
    for carpeta in respuesta.get("files"):
        if carpeta.get("name") == "TP_2Algo15":
            return carpeta.get("id")

    meta_carpeta = {  # Esto se podria hacer una funcion para crear carpetas
        "name": "TP_2Algo15",
        "mimeType": "application/vnd.google-apps.folder",
    }
    carpeta = (
        service_drive.obtener_servicio()
        .files()
        .create(body=meta_carpeta, fields="id")
        .execute()
    )
    return carpeta.get("id")


ROOT_DRIVE = (
    root_drive()
)  # Variable global porque no tendria sentido salirse de esta carpeta


def ver_archivos(path: str) -> None:  # Esta parte puede servir para otras funciones.
    directorio = os.listdir(path)
    for archivo in directorio:
        print(archivo)


def archivos_local() -> None:
    selector = str()
    path = os.getcwd()  # Esto es valido si la carpeta principal es donde esta el .py.
    while not selector == "salir":
        clear()
        ver_archivos(path)
        selector = input(
            """
        Ingrese la carpeta a la que quiera ingresar,
        atras para volver al directorio anterior,
        salir para volver al menu principal: """
        )
        if selector == "atras":
            path = os.path.dirname(path)
        else:
            if os.path.isdir(os.path.join(path, selector)):
                path = os.path.join(path, selector)


def archivos_remoto() -> None:
    id_carpeta = ROOT_DRIVE
    selector = str()
    while not selector == "salir":
        clear()
        query = f"parents = '{id_carpeta}'"
        field = "files(id, name, mimeType)"
        respuesta = (
            service_drive.obtener_servicio()
            .files()
            .list(q=query, fields=field)
            .execute()
        )
        for archivo in respuesta.get("files"):
            print(archivo.get("name"))
        selector = input(
            """
        Ingrese la carpeta a la que quiera ingresar,
        root para volver al directorio principal,
        salir para volver al menu principal: """
        )
        if selector == "root":
            id_carpeta = ROOT_DRIVE
        else:
            for archivo in respuesta.get("files"):
                if (
                    archivo.get("name") == selector
                    and archivo.get("mimeType") == "application/vnd.google-apps.folder"
                ):
                    id_carpeta = archivo.get("id")


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
        if selector == "1":  # a arbitrario por ahora.
            selector = input("Ingrese 1 para Local, 2 para Remoto: ")
            if selector == "1":
                archivos_local()
            if selector == "2":
                archivos_remoto()
        if selector == "2":
            pass
        if selector == "3":
            pass
        if selector == "4":
            pass
        if selector == "5":
            pass
        if selector == "6":
            pass
        if selector == "7":
            pass


main()
