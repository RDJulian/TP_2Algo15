import os


def ver_archivos(path: str) -> None:  # Esta parte puede servir para otras funciones.
    directorios = os.listdir(path)
    print("")
    for archivo in directorios:
        print(archivo)


def archivos_local() -> None:
    selector = str()
    path = os.getcwd()
    while not selector == "salir":
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
            else:
                print("\nLa carpeta no existe, intente nuevamente.")


def archivos_remoto() -> None:
    pass


def main() -> None:
    selector = str()
    while not selector == "8":
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
            a = str()
            a = input("1 Local, 2 Remoto: ")
            if a == "1":
                archivos_local()
            if a == "2":
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
