import os
import service_drive
import service_gmail


def clear() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def crear_carpeta_remota(nombre: str, id_carpeta: str) -> str:
    meta_carpeta = {
        "name": f"{nombre}",
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [id_carpeta],
    }
    carpeta = (
        service_drive.obtener_servicio()
        .files()
        .create(body=meta_carpeta, fields="id")
        .execute()
    )
    return carpeta.get("id")  # Capaz es mejor retornar toda la respuesta


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


def ver_archivos_remoto(id_carpeta: str) -> None:
    query = f"parents = '{id_carpeta}'"
    field = "files(id, name, mimeType)"
    respuesta = (
        service_drive.obtener_servicio().files().list(q=query, fields=field).execute()
    )
    for archivo in respuesta.get("files"):
        print(archivo.get("name"))
    return respuesta


def archivos_remoto() -> None:
    id_carpeta = ROOT_DRIVE
    selector = str()
    while not selector == "salir":
        clear()
        respuesta = ver_archivos_remoto(id_carpeta)
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


def carpetas_anidadas_remoto(
    path: str,
) -> str:  # Crea carpetas automaticamente si no existen en Drive
    anidacion = []
    while not os.path.split(path)[1] == os.path.split(os.getcwd())[1]:
        anidacion.insert(0, os.path.split(path)[1])
        path = os.path.split(path)[0]

    id_carpeta = ROOT_DRIVE
    while not anidacion == []:
        query = f"mimeType = 'application/vnd.google-apps.folder' and parents = '{id_carpeta}'"
        field = "files(id, name)"
        respuesta = (
            service_drive.obtener_servicio()
            .files()
            .list(q=query, fields=field)
            .execute()
        )

        idCarpetaAux = str()
        for carpeta in respuesta.get("files"):
            if carpeta.get("name") == anidacion[0]:
                idCarpetaAux = carpeta.get("id")

        if idCarpetaAux != "":
            id_carpeta = idCarpetaAux
            anidacion.pop(0)
        else:
            id_carpeta = crear_carpeta_remota(anidacion[0], id_carpeta)
            anidacion.pop(0)

    return id_carpeta


def crear_carpeta():  # Muy parecido a ver_archivos
    selector = str()
    path = os.getcwd()
    while not (selector == "salir" or selector == "crear"):
        clear()
        ver_archivos(path)
        selector = input(
            """
        Ingrese la carpeta a donde quiera moverse,
        crear para crear la carpeta en este directorio,
        atras para volver al directorio anterior,
        salir para volver al menu principal: """
        )
        if selector == "atras":
            path = os.path.dirname(path)
        elif selector == "crear":
            nombre = input("\nIngrese el nombre de la carpeta: ")
            os.mkdir(os.path.join(path, nombre))
            id = carpetas_anidadas_remoto(path)
            crear_carpeta_remota(nombre, id)
        else:
            if os.path.isdir(os.path.join(path, selector)):
                path = os.path.join(path, selector)


def crear_archivo():
    pass


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
                archivos_local()
            if opcion == "2":
                archivos_remoto()
        if selector == "2":
            opcion = input(
                "Ingrese 1 para crear una carpeta, 2 para crear un archivo: "
            )
            if opcion == "1":
                crear_carpeta()
            if opcion == "2":
                crear_archivo()
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
