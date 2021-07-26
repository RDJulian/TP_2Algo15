import service_gmail
import service_drive
import io
import base64
from googleapiclient.http import MediaIoBaseUpload
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def mandar_email(receptor: str, asunto: str, cuerpo: str)-> None:
    mensaje_mime = MIMEMultipart()
    mensaje_mime['to'] = receptor
    mensaje_mime['subject'] = asunto
    mensaje_mime.attach(MIMEText(cuerpo, "plain"))
    cadena_bytes = base64.urlsafe_b64encode(mensaje_mime.as_bytes()).decode()
    service_gmail.obtener_servicio().users().messages().send(userId='me', body={'raw': cadena_bytes}).execute()


def buscar(query, label_ids):
    lista_mensajes = service_gmail.obtener_servicio().users().messages().list(
        userId="me",
        labelIds=label_ids,
        q=query
    ).execute()
    id_mensaje = lista_mensajes.get("messages")
    return id_mensaje


def obtener_datos_mensaje(id_mensaje):
    datos_mensaje = service_gmail.obtener_servicio().users().messages().get(
        userId="me",
        id=id_mensaje,
    ).execute()

    return datos_mensaje


def descargar_adjunto(id_carpeta:str, payload_mensaje:dict, id_mensaje: str):

    if "parts" in payload_mensaje:
        for item in payload_mensaje["parts"]:
            nombre_archivo = item["filename"]
            cuerpo = item["body"]
            mime_type = item["mimeType"]
            if "attachmentId" in cuerpo:
                id_adjunto = cuerpo['attachmentId']
                respuesta = service_gmail.obtener_servicio().users().messages().attachments().get(
                    userId = "me",
                    messageId=id_mensaje,
                    id = id_adjunto
                ).execute()

                archivo = base64.urlsafe_b64decode(
                    respuesta.get("data").encode("UTF-8")
                )
                bytes = io.BytesIO(archivo)

                metadata = {"name": nombre_archivo, "parents": [id_carpeta]}

                media = MediaIoBaseUpload(bytes, mimetype=mime_type)

                service_drive.obtener_servicio().files().create(
                    body=metadata, media_body=media, fields="id").execute()



def mensajes() -> None:
    mensajes = buscar("has:attachment", ["INBOX"])
    for mensaje in mensajes:
        id_mensaje = mensaje["id"]
        datos_mensaje = obtener_datos_mensaje(mensaje["id"])
        payload_mensaje = datos_mensaje.get("payload")
        print(payload_mensaje)
        for item in payload_mensaje["headers"]:
            if item["name"] == "Return-Path":
                remitente = item["value"]
            if item["name"] == "Subject":
                asunto = item["value"]

        descargar_adjunto(id_carpeta, payload_mensaje,id_mensaje)

mensajes()