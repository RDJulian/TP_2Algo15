import os
import service_drive
import service_gmail
from hashlib import md5
from io import BytesIO
from datetime import datetime
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from csv import reader
from zipfile import ZipFile


EXTENSIONES_VALIDAS = [
    "txt",
    "jpg",
    "py",
    "pdf",
    "zip",
    "docx",
]  # Se pueden agregar mas

CARACTERES_ILEGALES = [
    "#",
    "<",
    "$",
    "%",
    ">",
    "!",
    "&",
    "*",
    "'",
    "{",
    "?",
    '"',
    "}",
    "/",
    ":",
    "@",
    "+",
    "`",
    "|",
    "=",
]


def clear() -> None:
    """PRE:
    POST:
    """
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def crear_carpeta_remota(nombre: str, idCarpeta: str) -> str:
    """PRE: Ingresa el nombre de la carpeta y el id del parent.
    POST: Genera la carpeta y devuelve el id.
    """
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
    return carpeta.get("id")


def root_drive() -> str:  # Esta funcion crea una carpeta tipo root para todos los archivos del trabajo
    """PRE:
    POST: Devuelve el id de la carpeta.
    """
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
    """PRE:
    POST: Devuelve el path de la carpeta.
    """
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


def ver_archivos(path: str) -> None:
    """PRE: Ingresa el path de la carpeta a mostrar.
    POST:
    """
    directorio = os.listdir(path)
    for archivo in directorio:
        print(archivo)


def ver_archivos_remoto(idCarpeta: str) -> dict:
    """PRE: Ingresa el id de la carpeta a mostrar.
    POST: Devuelve la respuesta de la API.
    """
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
    """PRE: Ingresa el path de la carpeta objetivo.
    POST: Devuelve el id de la carpeta objetivo creada en Drive.
    """
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


def subir_archivo(path: str, nombre: str, idCarpeta: str) -> None:
    """PRE: Ingresa el path entero, el nombre del archivo y el id de la carpeta objetivo.
    POST:
    """
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


def descargar_archivo(idArchivo: str, tipo: str, nombre: str, path: str) -> None:
    """PRE: Ingresa el id del archivo, su mimeType, el nombre y el path objetivo.
    POST:
    """
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
        bytes = BytesIO()
        respuesta = service_drive.obtener_servicio().files().get_media(fileId=idArchivo)
        descarga = MediaIoBaseDownload(bytes, respuesta)

        completo = False
        while not completo:
            _, completo = descarga.next_chunk()
        bytes.seek(0)

        with open(os.path.join(path, nombre), "wb") as archivo:
            archivo.write(bytes.read())


def chequeo_nombre(nombre: str) -> bool:
    """PRE: Ingresa el nombre de un archivo.
    POST: Devuelve un bool dependiendo de si contiene un caracter ilegal.
    """
    for caracter in CARACTERES_ILEGALES:
        if caracter in nombre:
            return False
    return True


def navegador_local() -> None:  # ESTA ES LA PRINCIPAL PARA LOCAL
    """PRE:
    POST:
    """
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
                while not chequeo_nombre(nombre):
                    nombre = input("Ingrese un nombre valido: ")

                os.mkdir(os.path.join(path, nombre))
                idCarpeta = anidar_carpetas_remoto(path)
                crear_carpeta_remota(nombre, idCarpeta)

            if opcion == "2":
                nombre = input("Ingrese el nombre del archivo: ")
                while not chequeo_nombre(nombre):
                    nombre = input("Ingrese un nombre valido: ")

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

            existente = bool()
            for archivo in respuesta.get("files"):
                if nombre == archivo.get("name"):
                    existente = True
                    archivoExistente = archivo.get("id")

            if existente:
                decision = input(
                    "Se encontro un archivo con el mismo nombre, ¿quiere sobrescribirlo? si/no: "
                )
                if decision == "si":
                    service_drive.obtener_servicio().files().delete(
                        fileId=archivoExistente
                    ).execute()
                    subir_archivo(os.path.join(path, nombre), nombre, idCarpeta)
            else:
                subir_archivo(os.path.join(path, nombre), nombre, idCarpeta)

        else:
            if os.path.isdir(os.path.join(path, selector)):
                path = os.path.join(path, selector)


def navegador_remoto() -> None:  # ESTA ES LA PRINCIPAL PARA REMOTO
    """PRE:
    POST:
    """
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

            existente = bool()
            for archivo in os.listdir(path):
                if nombre == archivo:
                    existente = True

            if existente:
                decision = input(
                    "Se encontro un archivo con el mismo nombre, ¿quiere sobrescribirlo? si/no: "
                )
                if decision == "si":
                    descargar_archivo(idArchivo, tipo, nombre, path)
            else:
                descargar_archivo(idArchivo, tipo, nombre, path)

        else:
            for archivo in respuesta.get("files"):
                if (
                    archivo.get("name") == selector
                    and archivo.get("mimeType") == "application/vnd.google-apps.folder"
                ):
                    idCarpeta = archivo.get("id")


def sincronizar(idCarpeta: str, path: str) -> None:
    """PRE: Ingresa el id de carpeta y el path a comparar.
    POST:
    """
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
            checksumLocal = md5(open(f"{pathArchivo}", "rb").read()).hexdigest()
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


def descomprimir(file_zip: str, directorio: str, id_carpeta: str) -> None:
    """PRE: Ingresa el nombre del .zip, el directorio y el id de la carpeta a subir.
    POST:
    """
    path = os.path.join(directorio, file_zip)
    with ZipFile(path, "r") as zip_ref:
        zip_ref.extractall(directorio)
    os.remove(path)
    carpeta = os.listdir(directorio)
    for archivo in carpeta:
        path = os.path.join(directorio, archivo)
        subir_archivo(path, archivo, id_carpeta)


def mandar_email(receptor: str, asunto: str, cuerpo: str) -> None:
    """PRE: Ingresa el mail receptor, el asunto y el cuerpo del mail.
    POST:
    """
    mensaje_mime = MIMEMultipart()
    mensaje_mime["to"] = receptor
    mensaje_mime["subject"] = asunto
    mensaje_mime.attach(MIMEText(cuerpo, "plain"))
    cadena_bytes = urlsafe_b64encode(mensaje_mime.as_bytes()).decode()
    service_gmail.obtener_servicio().users().messages().send(
        userId="me", body={"raw": cadena_bytes}
    ).execute()


def buscar(query: str, label_ids: str) -> dict:
    """PRE: Ingresa las condiciones de query y label_ids.
    POST: Devuelve un diccionario con las respuestas matcheadas.
    """
    lista_mensajes = (
        service_gmail.obtener_servicio()
        .users()
        .messages()
        .list(userId="me", labelIds=label_ids, q=query)
        .execute()
    )
    id_mensajes = lista_mensajes.get("messages")
    return id_mensajes


def obtener_datos_mensaje(id_mensaje: str) -> dict:
    """PRE: Ingresa el id del mail.
    POST: Devuelve un diccionario con los datos del mail.
    """
    datos_mensaje = (
        service_gmail.obtener_servicio()
        .users()
        .messages()
        .get(
            userId="me",
            id=id_mensaje,
        )
        .execute()
    )
    return datos_mensaje


def descargar_adjunto(
    id_carpeta: str, payload_mensaje: dict, id_mensaje: str, path: str
) -> None:
    """PRE: Ingresa el id del mail, el id y el path de las carpetas objetivo y el payload del mensaje.
    POST:
    """
    if "parts" in payload_mensaje:
        for item in payload_mensaje["parts"]:
            nombre_archivo = item["filename"]
            cuerpo = item["body"]
            if "attachmentId" in cuerpo:
                id_adjunto = cuerpo["attachmentId"]
                respuesta = (
                    service_gmail.obtener_servicio()
                    .users()
                    .messages()
                    .attachments()
                    .get(userId="me", messageId=id_mensaje, id=id_adjunto)
                    .execute()
                )

                archivo_adjunto = urlsafe_b64decode(
                    respuesta.get("data").encode("UTF-8")
                )
                bytes = BytesIO(archivo_adjunto)
                bytes.seek(0)
                with open(os.path.join(path, nombre_archivo), "wb") as archivo:
                    archivo.write(bytes.read())

                if nombre_archivo.endswith(".zip"):
                    descomprimir(nombre_archivo, path, id_carpeta)
                else:
                    subir_archivo(
                        os.path.join(path, nombre_archivo), nombre_archivo, id_carpeta
                    )


def docentes_alumnos(path: str) -> dict:
    """PRE: Ingresa el path de la carpeta del examen.
    POST: Devuelve un diccionario con los datos del .csv.
    """
    ruta = os.path.join(path, "docente-alumnos.csv")
    diccDocAlu = dict()
    with open(ruta, mode="r", newline="", encoding="UTF-8") as archivo_csv:
        csv_reader = reader(archivo_csv, delimiter=",")
        next(csv_reader)
        for fila in csv_reader:
            docente = fila[0]
            alumno = fila[1]
            if docente in diccDocAlu:
                diccDocAlu[docente].append(alumno)
            else:
                diccDocAlu[docente] = [alumno]
    return diccDocAlu


def diccionario_alumnos(path: str) -> dict:
    """PRE: Ingresa el path de la carpeta del examen.
    POST: Devuelve un diccionario con los datos del .csv.
    """
    ruta = os.path.join(path, "alumnos.csv")
    nombre = 0
    padron = 1
    mail = 2
    diccAlumnos = dict()
    with open(ruta, mode="r", newline="", encoding="UTF-8") as archivo_csv:
        csv_reader = reader(archivo_csv, delimiter=",")
        next(csv_reader)
        for fila in csv_reader:
            diccAlumnos[fila[padron]] = [fila[nombre], fila[mail]]
    return diccAlumnos


def carpetas_docentes(path: str, carpeta_id: str) -> None:
    """PRE: Ingresa el path y el id de las carpetas del examen.
    POST:
    """
    ruta = os.path.join(path, "docentes.csv")
    nombre = 0
    diccDocAlu = docentes_alumnos(path)
    diccAlumnos = diccionario_alumnos(path)
    with open(ruta, mode="r", newline="", encoding="UTF-8") as archivo_csv:
        csv_reader = reader(archivo_csv, delimiter=",")
        next(csv_reader)
        for fila in csv_reader:
            docente = fila[nombre]
            id = crear_carpeta_remota(docente, carpeta_id)
            if docente in diccDocAlu.keys():
                for alumno in diccDocAlu[docente]:
                    crear_carpeta_remota(alumno, id)

    id = crear_carpeta_remota("sin_docente", carpeta_id)
    alumnos_asignados = list()
    for docente in diccDocAlu:
        for alumno in diccDocAlu[docente]:
            alumnos_asignados.append(alumno)
    for padron in diccAlumnos:
        alumno = diccAlumnos[padron][nombre]
        if alumno not in alumnos_asignados:
            crear_carpeta_remota(alumno, id)


def generar_carpetas_evaluacion() -> None:
    """PRE:
    POST:
    """
    mensajes = buscar("has:attachment", "INBOX")
    for mensaje in mensajes:
        datos_mensaje = obtener_datos_mensaje(mensaje["id"])
        payload_mensaje = datos_mensaje.get("payload")
        asunto = str()
        evaluacion = bool()
        for item in payload_mensaje["headers"]:
            if item["name"] == "Subject":
                asunto = item["value"]
        if "parts" in payload_mensaje:
            for item in payload_mensaje["parts"]:
                nombre_archivo = item["filename"]
                if nombre_archivo.endswith(".csv"):
                    evaluacion = True
            if evaluacion:
                query = f"mimeType = 'application/vnd.google-apps.folder' and parents = '{ROOT_DRIVE}'"
                field = "files(id, name)"
                respuesta = (
                    service_drive.obtener_servicio()
                    .files()
                    .list(q=query, fields=field)
                    .execute()
                )

                directorioLocal = os.listdir(ROOT_LOCAL)
                lista_carpetas = list()

                for carpeta in respuesta.get("files"):
                    lista_carpetas.append(carpeta.get("name"))

                if (
                    asunto not in lista_carpetas and asunto not in directorioLocal
                ):  # Para evitar sobrescribir
                    path = os.path.join(ROOT_LOCAL, asunto)
                    os.mkdir(path)
                    carpeta_id = crear_carpeta_remota(asunto, ROOT_DRIVE)

                    descargar_adjunto(carpeta_id, payload_mensaje, mensaje["id"], path)
                    directorioExamen = os.listdir(path)

                    if (
                        "alumnos.csv" in directorioExamen
                        and "docentes.csv" in directorioExamen
                        and "docente-alumnos.csv" in directorioExamen
                    ):
                        carpetas_docentes(path, carpeta_id)
                        descargar_archivo(
                            carpeta_id,
                            "application/vnd.google-apps.folder",
                            asunto,
                            ROOT_LOCAL,
                        )


def validar_entrega(padron: str, path: str, payload_mensaje: dict) -> tuple:
    """PRE: Ingresa el padron del alumno, el path de la carpeta del examen y el payload del mail.
    POST: Devuelve una tupla con un bool sobre la entrega y el mensaje a reenviar.
    """
    alumnos = diccionario_alumnos(path)
    entrega = False
    mensaje = str()
    archivos = str()
    if "parts" in payload_mensaje:
        for item in payload_mensaje["parts"]:
            nombre_archivo = item["filename"]
            archivos += nombre_archivo
            if nombre_archivo.endswith(".zip") and padron in alumnos:
                mensaje = "Entrega OK"
                entrega = True
        if len(archivos) == 0:
            mensaje += "No tiene adjunto.\n"
        elif not ".zip" in archivos:
            mensaje += "El adjunto no es un archivo zip.\n"
    if padron not in alumnos:
        mensaje += "Padron incorrecto."
    return (entrega, mensaje)


def buscar_carpeta(path: str, carpeta_id: str, alumno: str) -> str:
    """PRE: Ingresa el path y el id de las carpetas del examen, y el nombre del alumno.
    POST: Devuelve el id de la carpeta del alumno.
    """
    docentes_alumnos_dicc = docentes_alumnos(path)
    carpeta_docente = str()
    carpeta_alumno_id = list()
    carpeta = "sin_docente"
    for docente in docentes_alumnos_dicc:
        for persona in docentes_alumnos_dicc[docente]:
            if persona == alumno:
                carpeta = docente

    query = (
        f"mimeType = 'application/vnd.google-apps.folder' and parents = '{carpeta_id}'"
    )
    field = "files(id, name)"
    respuesta = (
        service_drive.obtener_servicio().files().list(q=query, fields=field).execute()
    )
    for archivo in respuesta.get("files"):
        if archivo.get("name") == carpeta:
            carpeta_docente = archivo.get("id")

    query = f"mimeType = 'application/vnd.google-apps.folder' and parents = '{carpeta_docente}'"
    field = "files(id, name)"
    respuesta = (
        service_drive.obtener_servicio().files().list(q=query, fields=field).execute()
    )
    for carpeta in respuesta.get("files"):
        if carpeta.get("name") == alumno:
            carpeta_alumno_id = carpeta.get("id")

    return carpeta_alumno_id


def buscar_directorio(path: str, alumno: str) -> str:
    """PRE: Ingresa el path de la carpeta del examen y el nombre del alumno.
    POST: Devuelve el path de la carpeta del alumno.
    """
    docentes_alumnos_dicc = docentes_alumnos(path)
    carpeta = "sin_docente"
    for docente in docentes_alumnos_dicc:
        for persona in docentes_alumnos_dicc[docente]:
            if persona == alumno:
                carpeta = docente
    carpeta_docente = os.path.join(path, carpeta)
    carpeta_alumno = os.path.join(carpeta_docente, alumno)
    return carpeta_alumno


def lista_mail(path: str) -> list:
    """PRE: Ingresa el path de la carpeta del examen.
    POST: Devuelve una lista con todos los mails de los alumnos.
    """
    diccAlumnos = diccionario_alumnos(path)
    lista = list()
    for padron in diccAlumnos:
        lista.append(diccAlumnos[padron][1])
    return lista


def asignacion_archivos(carpeta_id: str, path: str) -> None:
    """PRE: Ingresa el id y el path de las carpetas del examen.
    POST:
    """
    mensajes = buscar("", "INBOX")
    dicc_alumnos = diccionario_alumnos(path)
    mail_alumnos = lista_mail(path)
    for mensaje in mensajes:
        datos_mensaje = obtener_datos_mensaje(mensaje["id"])
        payload_mensaje = datos_mensaje.get("payload")
        entrega = bool()
        remitente = str()
        padron = str()
        for item in payload_mensaje["headers"]:
            if item["name"] == "Subject":
                padron = item["value"]
            if item["name"] == "From":
                remitente = item["value"].split()[-1]
                mail = remitente[1:-1]
                if mail in mail_alumnos:
                    entrega = True

        if entrega:
            valido = validar_entrega(padron, path, payload_mensaje)[0]
            respuesta = validar_entrega(padron, path, payload_mensaje)[1]
            if valido:
                alumno = dicc_alumnos[padron][0]
                carpeta = buscar_directorio(path, alumno)
                if len(os.listdir(carpeta)) == 0:  # Si no hizo una entrega
                    mandar_email(remitente, "Retroalimentación", respuesta)
                    id_carpeta = buscar_carpeta(path, carpeta_id, alumno)
                    descargar_adjunto(
                        id_carpeta, payload_mensaje, mensaje["id"], carpeta
                    )


def asignacion() -> None:
    """PRE:
    POST:
    """
    nombre = input("Escriba el nombre de la evaluación։ ")
    carpeta_local = os.path.join(ROOT_LOCAL, nombre)
    if os.path.isdir(carpeta_local):  # No es necesario pero por las dudas
        query = f"mimeType = 'application/vnd.google-apps.folder' and parents = '{ROOT_DRIVE}'"
        field = "files(id, name)"
        respuesta = (
            service_drive.obtener_servicio()
            .files()
            .list(q=query, fields=field)
            .execute()
        )
        carpeta_id = str()
        for archivo in respuesta.get("files"):
            if archivo.get("name") == nombre:
                carpeta_id = archivo.get("id")
        asignacion_archivos(carpeta_id, carpeta_local)


def main() -> None:
    """PRE:
    POST:
    """
    selector = str()
    while not selector == "8":
        clear()
        print(
            """
        1. Listar archivos de la carpeta actual
        2. Crear un archivo
        3. Subir un archivo
        4. Descargar un archivo
        5. Sincronizar
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
            generar_carpetas_evaluacion()

        elif selector == "7":
            asignacion()


main()
