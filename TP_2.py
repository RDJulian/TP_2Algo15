import os
import service_drive
from googleapiclient.http import MediaFileUpload

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






def elegir_archivo_local()-> str:

    directorio_origen = os.getcwd()
    path = os.getcwd()
    path_archivo = str()
    entrar = True
    while entrar:
        ver_archivos(path)
        opcion = input("1. Elegir un archivo/ 2. Entrar a una carpeta/ 3. Atras: ")
        if opcion == "1":
            archivo = input("Elige el nombre del archivo: ")
            path_archivo = os.path.join(path, archivo)
            if os.path.isfile(path_archivo) == True:
                entrar = False
            else:
                print("El nombre elegido no es un archivo, elige nuevamente")
        elif opcion == "2":
            carpeta = input("Ingrese el nombre de la carpeta: ")
            if os.path.isdir(os.path.join(path, carpeta)):
                path = os.path.join(path, carpeta)
            else:
                print("El nombre elegido no es una carpeta, elige nuevamente")
        else:
             path = os.path.dirname(path)
    return path_archivo


def elegir_carpeta_drive()-> str:
    id_carpeta = ROOT_DRIVE
    id_carpeta_subir = str()
    seguir = True
    while seguir:
        respuesta = ver_archivos_remoto(id_carpeta))
        opcion = input("1. Elegir una carpeta/ 2. Entrar a una carpeta/ 3. Volver al directorio principal: " )
        if opcion == "1":
            carpeta = input("Ingrese el nombre de la carpeta: ")
            for archivo in respuesta.get("files"):
                if archivo.get("name") == carpeta and archivo.get("mimeType")==  "application/vnd.google-apps.folder":
                    id_carpeta_subir = archivo.get("id")
                    seguir = False

        elif opcion == "3":
            id_carpeta = ROOT_DRIVE
        else:
            carpeta = input("Elige el nombre de la carpeta")
            for archivo in respuesta.get("files"):
                if (
                    archivo.get("name") == carpeta
                and archivo.get("mimeType") == "application/vnd.google-apps.folder"):
                    id_carpeta = archivo.get("id")

    return id_carpeta_subir


def subir_archivo()-> None:
    nombre = elegir_archivo_local()
    carpeta_id = elegir_carpeta_drive()
    file_metadata = {'name': nombre, "parents": [carpeta_id]}

    media = MediaFileUpload(nombre)
    service_drive.obtener_servicio().files().create(body=file_metadata,
                                     media_body=media,fields='id').execute()
    print(f"El archivo {nombre} se subió correctamente")


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
            subir_archivo()
        if selector == "4":
            pass
        if selector == "5":
            pass
        if selector == "6":
            pass
        if selector == "7":
            pass


main()
