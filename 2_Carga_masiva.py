import requests
import json
import os
# from Convertir_xlsx_json import convertir_Json

# IDs y URL del Asset
uuaid = "adohUsoAUkY9fKPyfgt49k"  # ID del asset en KoboToolbox
url_base = f"https://eu.kobotoolbox.org/api/v2/assets/{uuaid}/data/"
url_bulk = f"https://eu.kobotoolbox.org/api/v2/assets/{uuaid}/data/bulk/"  # URL correcta para la actualización masiva

# Leer las credenciales desde el archivo config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Obtener el token de autenticación
token = config.get('KOBO_API_TOKEN')
if not token:
    print("Error: El token de autenticación no está en el archivo de configuración.")
    exit(1)

# Encabezados con el token de autenticación
headers = {
    "Authorization": f"Token {token}",
    "Content-Type": "application/json"
}

# Leer el archivo JSON que contiene los datos a actualizar
try:
    with open('datos_corregir.json', 'r', encoding='utf-8') as file:
        Cambios = json.load(file)
    print("Datos cargados exitosamente desde datos_corregir.json")
except FileNotFoundError:
    print("Error: El archivo datos_corregir.json no se encontró.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error: El archivo datos_corregir.json contiene errores de formato JSON. {e}")
    exit(1)

# Función para guardar la respuesta en un archivo json
def guardar_respuesta_en_json(submission_id):
    url = f"{url_base}{submission_id}/?format=json"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            archivo_json = f"{submission_id}.json"
            with open(archivo_json, 'w', encoding='utf-8') as file:
                file.write(response.text)
            print(f"Respuesta guardada en {archivo_json}")
            return archivo_json
        else:
            print(f"Error: {response.status_code} - {response.reason}")
            return None
    except Exception as e:
        print(f"Error al hacer la solicitud: {e}")
        return None

# Función para extraer el JSON del archivo
def extraer_json_de_archivo(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as file:
            contenido = file.read()
        try:
            datos_json = json.loads(contenido)
            return datos_json
        except json.JSONDecodeError:
            print("Error al decodificar JSON.")
            return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None

# Verificar si el _uuid del servidor coincide con el del JSON
# def verificar_uuid_en_kobo(submission_id, uuid_json):
#     archivo_json = guardar_respuesta_en_json(submission_id)
#     if archivo_json:
#         datos_kobo = extraer_json_de_archivo(archivo_json)
#         if datos_kobo:
#             uuid_kobo = datos_kobo.get('_uuid')
#             return uuid_kobo == uuid_json, uuid_kobo
#     return False, None

# Procesar cada cambio en el JSON
for idx, cambio in enumerate(Cambios, start=1):
    submission_ids = cambio.get("submission_ids", [])
    uuid_json = cambio["data"].get("_uuid")

    if not submission_ids or not uuid_json:
        print(f"Cambio {idx}: submission_ids o _uuid faltante. Saltando...")
        continue

    submission_id = submission_ids[0]  # Tomar el primer submission_id
    print(f"\nProcesando cambio {idx}/{len(Cambios)} para submission_id: {submission_id}...")

    # Verificar UUID en Kobo
    # coinciden, uuid_kobo = verificar_uuid_en_kobo(submission_id, uuid_json)
    # if coinciden:
    #     print(f"el _uuid si coincide con el _uuid de {submission_id}. se estan aplicando los cambio...")
        
        

    # Preparar el payload para la actualización masiva
    payload_to_send = {"payload": cambio}  # Aquí aseguramos que el cambio esté bien estructurado en el payload

    # Realizar la solicitud PATCH para la actualización masiva
    response = requests.patch(url_bulk, headers=headers, data=json.dumps(payload_to_send))


    archivo_json = f"{submission_id}.json"
    if os.path.exists(archivo_json):
        os.remove(archivo_json)  # Eliminar el archivo JSON
        print(f"Archivo {archivo_json} eliminado exitosamente.")

    if response.status_code == 200:
        print(f"Cambio {idx} aplicado exitosamente:", response.json())
            
            
    else:
        print(f"Error en el cambio {idx}: {response.status_code}, {response.text}")
# else:
#     print(
#         f"UUID no coincide para submission_id {submission_id}.\n"
#         f"UUID en datos_corregir: {uuid_json}\n"
#         f"UUID en Kobo: {uuid_kobo or 'No encontrado'}"
#     )

print("\nEl proceso ha terminado.")
