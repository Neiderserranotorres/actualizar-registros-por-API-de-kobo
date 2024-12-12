import pandas as pd
import json
from tkinter import Tk
from tkinter.filedialog import askopenfilename

def convertir_Json():
    # Configurar el diálogo para seleccionar el archivo
    def seleccionar_archivo():
        Tk().withdraw()  # Ocultar la ventana principal de Tkinter
        archivo = askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
        )
        if not archivo:
            raise ValueError("No se seleccionó ningún archivo.")
        return archivo

    # Seleccionar archivo
    print("Por favor selecciona el archivo Excel:")
    archivo_excel = seleccionar_archivo()
    print(f"Archivo seleccionado: {archivo_excel}")

    # Leer las hojas del archivo Excel
    hojas = pd.read_excel(archivo_excel, sheet_name=None)  # Leer todas las hojas

    # Verificar el número de hojas
    if len(hojas) == 0:
        raise ValueError("El archivo no contiene hojas válidas.")

    # Configurar claves principales
    clave_padre = '_id'
    clave_hijo = '_submission__id'

    def convertir_timestamps(df):
        return df.applymap(
            lambda x: x.isoformat() if isinstance(x, pd.Timestamp) and pd.notna(x) else ("" if pd.isna(x) else x)
    )

    cambios = []  # Lista para almacenar los cambios

    # Caso 1: Solo hay una hoja
    if len(hojas) == 1:
        # Convertir la hoja única
        nombre_hoja = list(hojas.keys())[0]
        hoja = convertir_timestamps(hojas[nombre_hoja])
        datos = hoja.to_dict(orient='records')

        for registro in datos:
            uuid = registro.get(clave_padre)
            if not uuid:
                continue
            entrada = {
                "submission_ids": [uuid],
                "data": {columna: valor for columna, valor in registro.items() if columna != clave_padre}
            }
            cambios.append(entrada)

    # Caso 2: Hay dos hojas (padre e hijo)
    elif len(hojas) >= 2:
        hoja_padre, hoja_hijo = list(hojas.values())
        hoja_padre = convertir_timestamps(hoja_padre)
        hoja_hijo = convertir_timestamps(hoja_hijo)

        datos_padre = hoja_padre.to_dict(orient='records')
        datos_hijo = hoja_hijo.to_dict(orient='records')

        # Crear un diccionario de hijos agrupados por el _submission__id
        hijos_por_id = {}
        for hijo in datos_hijo:
            uuid_hijo = hijo.get(clave_hijo)
            if uuid_hijo:
                hijos_por_id.setdefault(uuid_hijo, []).append(hijo)

        # Procesar los datos padre y asociar hijos correspondientes
        for padre in datos_padre:
            uuid_padre = padre.get(clave_padre)
            if not uuid_padre:
                continue

            entrada = {
                "submission_ids": [f'"{uuid_padre}"'],
                "data": {columna: valor for columna, valor in padre.items() if columna != clave_padre}
            }

            if uuid_padre in hijos_por_id:
                hijos = hijos_por_id[uuid_padre]
                num_hijos = len(hijos)
                entrada["data"]["B/Total_personas"] = str(num_hijos)
                entrada["data"]["B/B1_count"] = str(num_hijos)

                hijos_con_prefijo = []
                for hijo in hijos:
                    hijo_con_prefijo = {f"B/B1/{columna}": valor for columna, valor in hijo.items() if columna != clave_hijo}
                    hijos_con_prefijo.append(hijo_con_prefijo)

                entrada["data"]["B/B1"] = hijos_con_prefijo

            cambios.append(entrada)

    # Guardar el resultado en un archivo JSON
    nombre_json = 'datos_corregir.json'
    with open(nombre_json, 'w', encoding='utf-8') as archivo_json:
        json.dump(cambios, archivo_json, ensure_ascii=False, indent=4)

    print(f"Proceso completo. Archivo guardado como {nombre_json}.")

# Llamada a la función
convertir_Json()
