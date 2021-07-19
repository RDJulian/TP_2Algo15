from service_drive import obtener_servicio
from googleapiclient.http import MediaFileUpload


def subir_archivo(name: str, parents: str, mimetype: str ):


    file_metadata = {'name': name, "parents": [parents]}

    media = MediaFileUpload(name, mimetype=mimetype)
    obtener_servicio().files().create(body=file_metadata,
                                    media_body=media).execute()


subir_archivo('23223.jpg', "1M1YndtPMJaiL5LZRlmbEl4w7KWAAJlyN", 'image/jpeg')
