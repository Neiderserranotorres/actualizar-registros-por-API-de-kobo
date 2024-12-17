import requests 
import json
import os
from Convertir_a_json import convertir_Json

# IDs y URL del Asset
uuaid = "aqui va el uuaid de la encuesta"  # ID del asset en KoboToolbox
url_base = f"https://eu.kobotoolbox.org/api/v2/assets/{uuaid}/data/"
url_bulk = f"https://eu.kobotoolbox.org/api/v2/assets/{uuaid}/data/bulk/"  # URL correcta para la actualización masiva


errores_xlsx = "errores_cambios.xlsx"
## Eliminar el archivo si existe
if os.path.exists(errores_xlsx):
    print(f"El archivo {errores_xlsx} existe. Procediendo a eliminarlo...")
    os.remove(errores_xlsx)  # Eliminación definitiva, como si presionaras Shift+Supr
    print(f"Archivo {errores_xlsx} eliminado exitosamente.")
else:
    print(f"El archivo {errores_xlsx} no existe, no es necesario eliminarlo.")

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

# Procesar cada cambio en el JSON
for idx, cambio in enumerate(Cambios, start=1):
    submission_ids = cambio.get("submission_ids", [])
    #     continue Ya no quiero que tenga en cuenta los _uuid para 
    submission_id = submission_ids[0]  # Tomar el primer submission_id
    print(f"\nProcesando cambio {idx}/{len(Cambios)} para submission_id: {submission_id}")
    
    # Preparar el payload para la actualización masiva
    payload_to_send = {"payload": cambio}  # Aquí aseguramos que el cambio esté bien estructurado en el payload
    # Realizar la solicitud PATCH para la actualización masiva
    response = requests.patch(url_bulk, headers=headers, data=json.dumps(payload_to_send))
    # Si la respuesta es 200, todo fue correcto
    if response.status_code == 200:
        print(f"Cambio {idx} aplicado exitosamente")
    else:
        errores_xlsx = "errores_cambios.xlsx"
        if not os.path.exists(errores_xlsx):
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Errores de Cambios"
            encabezados = ["_id", "Código de Error", "Tipo de Error", "Razón del Error", "Sugerencias"]
            sheet.append(encabezados)
            workbook.save(errores_xlsx)
        # Identificar el tipo de error y razón posible
        tipo_error = "Error de envío al servidor"
        if response.status_code == 400:
            razon_error = (
                "El _id no existe."
            )
        elif response.status_code == 403:
            razon_error = (
                "Permiso denegado. Esto puede ocurrir si las credenciales del usuario no tienen los permisos adecuados."
            )
        elif response.status_code == 500:
            razon_error = (
                "Error interno del servidor. Intenta nuevamente más tarde o contacta al soporte técnico."
            )
        else:
            razon_error = f"Error desconocido: {response.status_code}. Verifique el mensaje del servidor."
        # Abrir el archivo Excel para agregar errores
        workbook = openpyxl.load_workbook(errores_xlsx)
        sheet = workbook.active
        # Agregar el error al archivo Excel
        error_fila = [
            submission_id,           # _id completo
            response.status_code,    # Código de error
            tipo_error,              # Tipo de error
            razon_error,             # Razón del error
            "Por favor verifica el ID y vuelve a intentarlo.",  # Sugerencia para el usuario
        ]
        sheet.append(error_fila)
        # Guardar el archivo Excel con el error agregado
        workbook.save(errores_xlsx)
        print(f"Se presentó un error. Verifica el archivo generado de errores.")
print("\nEl proceso ha terminado.")
