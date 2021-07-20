import os
import service_drive
import service_gmail

EXTENSIONES_VALIDAS = ["txt", "jpg", "mp3", "mp4", "pdf"]  # Se pueden agregar


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


def ver_archivos_remoto(idCarpeta: str) -> None:
    query = f"parents = '{idCarpeta}'"
    field = "files(id, name, mimeType)"
    respuesta = (
        service_drive.obtener_servicio().files().list(q=query, fields=field).execute()
    )
    for archivo in respuesta.get("files"):
        print(archivo.get("name"))
    return respuesta


def archivos_remoto() -> None:  # ¿Cual es el punto de esta funcion? crear_carpeta_archivo hace lo mismo
    idCarpeta = ROOT_DRIVE
    selector = str()
    while not selector == "salir":
        clear()
        respuesta = ver_archivos_remoto(idCarpeta)
        selector = input(
            """
        Ingrese la carpeta a la que quiera ingresar,
        root para volver al directorio principal,
        salir para volver al menu principal: """
        )
        if selector == "root":
            idCarpeta = ROOT_DRIVE
        else:
            for archivo in respuesta.get("files"):
                if (
                    archivo.get("name") == selector
                    and archivo.get("mimeType") == "application/vnd.google-apps.folder"
                ):
                    idCarpeta = archivo.get("id")


def anidar_carpetas_remoto(
    path: str,
) -> str:  # Crea carpetas automaticamente si no existen en Drive
    anidacion = []
    while not os.path.split(path)[1] == os.path.split(os.getcwd())[1]:
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


def crear_archivo_remoto():
    pass


def crear_archivo():  # Muy parecido a archivos_remoto
    selector = str()
    path = os.getcwd()
    while not selector == "salir":
        clear()
        ver_archivos(path)
        selector = input(  # Esto se podria mejorar para que sea mas intuitivo
            """
        Ingrese la carpeta a donde quiera moverse,
        crear para crear el archivo en este directorio,
        atras para volver al directorio anterior,
        salir para volver al menu principal: """
        )
        if selector == "atras":
            path = os.path.dirname(path)
        elif selector == "crear":
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
                    extension = input("Ingrese una extension valida")
                nombreExtension = f"{os.path.join(path,nombre)}.{extension}"
                with open(nombreExtension, "w") as _:
                    pass  # FALTA SUBIR EL ARCHIVO
        else:
            if os.path.isdir(os.path.join(path, selector)):
                path = os.path.join(path, selector)


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
