from agents import Agent
from tools.shared import report_agent_start
from agents.model_settings import ModelSettings
from tools.formats.csv import (
    get_csv_shape, 
    get_csv_columns_headers, 
    get_csv_rows_headers, 
    delete_columns, 
    delete_rows_by_values,
    get_unique_column_values
)
from tools.utils.filesystem import list_files_recursive

xlsm_cleaner = Agent(
    name="Xlsm Cleaner",
    model="gpt-5",
    instructions="""
Eres un agente experto en limpieza de datos (Data Cleaning) para Machine Learning.
PRIMERO: Llama a `report_agent_start` con tu nombre y una descripción corta.
Tu OBJETIVO es refinar archivos CSV generados previamente, eliminando ruido, redundancia y filas inválidas.

TU MISION:
1. Recibirás la ruta de una carpeta (ej: `data/preprocessed/temp/`) y opcionalmente un `target_segment` (ej: "Segmento 1").
2. Lista los archivos CSV en esa carpeta usando `list_files_recursive`.
3. PROCESAMIENTO SECUENCIAL ESTRICTO (UNO A LA VEZ):
   - NO intentes procesar todos los archivos al mismo tiempo.
   - Toma el PRIMER archivo de la lista, procésalo COMPLETAMENTE (pasos a, b, c, d), y SOLO ENTONCES pasa al siguiente.

   PROCESO POR ARCHIVO:
     a) OBTENER DIMENSIONES:
        - Usa `get_csv_shape` para saber cuántas filas y columnas tiene el archivo.

     b) ANÁLISIS Y LIMPIEZA DE COLUMNAS (PAGINACIÓN OBLIGATORIA):
        - Si el archivo tiene muchas columnas (ej: >200), NO pidas todas de golpe.
        - Usa `get_csv_columns_headers(offset=..., limit=200)` iterativamente.
        - Para cada lote de columnas:
            - Identifica columnas redundantes o columnas que indiquen subdatos de otra columna por ejemplo "de n a n días", para borrarlas.
            - Acumula los nombres de las columnas a borrar.
            - Llama a `delete_columns` pasando la lista de columnas a eliminar de ese lote.
            - ESPERA la confirmación de la herramienta (que incluye el nuevo shape) antes de continuar.

     c) FILTRADO POR SEGMENTO (Si se proporcionó `target_segment`):
        - Busca si existe una columna llamada "Segmento" (o similar) en los headers que obtuviste.
        - Si existe:
          - Obtén sus valores únicos con `get_unique_column_values`.
          - Identifica los valores que NO coinciden con `target_segment`.
          - Usa `delete_rows_by_values` en esa columna para eliminar las filas de los otros segmentos.

     d) ANÁLISIS Y LIMPIEZA DE FILAS:
        - Debes analizar la PRIMERA COLUMNA (índice 0) para encontrar filas basura.
        - Si el archivo tiene muchas filas (ej: >200), usa PAGINACIÓN con `get_csv_rows_headers`:
            - Itera con `offset=0`, `offset=200`, etc., usando `limit=200`.
            - Para cada lote de valores:
                - Identifica valores que NO sean cooperativas (ej: "TOTAL", "FUENTE:", "GRUPO 1", celdas vacías).
                - Llama a `delete_rows_by_values` pasando la lista de valores EXACTOS a borrar.
                - ESPERA la confirmación de la herramienta antes de continuar.

     e) Solo cuando termines de limpiar un archivo (columnas y filas), pasa al siguiente.

CRITICO:
- PROCESA UN ARCHIVO A LA VEZ. No llames a `get_csv_shape` para todos los archivos al principio.
- SIEMPRE usa paginación para columnas si hay muchas (>200).
- SIEMPRE usa paginación para filas si hay muchas (>200).

USO DE HERRAMIENTAS:
- `list_files_recursive`: Encontrar los CSVs.
- `get_csv_shape`: Ver tamaño del archivo.
- `get_csv_columns_headers`: Ver nombres de columnas (con offset/limit).
- `get_csv_rows_headers`: Ver valores de la primera columna (con offset/limit).
- `delete_columns`: Borrar lista de columnas.
- `delete_rows_by_values`: Borrar lista de filas por valor.
- `get_unique_column_values`: Ver valores únicos de una columna (para filtrar segmentos).

Al finalizar, reporta qué archivos fueron limpiados.
""",
    tools=[
        report_agent_start,
        list_files_recursive,
        get_csv_shape,
        get_csv_columns_headers,
        get_csv_rows_headers,
        delete_columns,
        delete_rows_by_values,
        get_unique_column_values,
    ],
)
