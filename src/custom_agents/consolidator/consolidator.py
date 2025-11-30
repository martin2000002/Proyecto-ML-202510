from agents import Agent
from tools.shared import report_agent_start
from tools.transform.dataset import (
    get_first_column,
    create_dataset,
    append_aligned_columns,
    append_cleaned_risk_column,
    finalize_and_clean_dataset
)
from tools.formats.csv import get_csv_columns_headers
from tools.utils.datetime import get_current_date

consolidator = Agent(
    name="Consolidator",
    model="gpt-5",
    instructions="""
Eres un agente encargado de construir el dataset final a partir de varios archivos CSV extraídos.
PRIMERO: Llama a `report_agent_start` con tu nombre y una descripción corta.
Tu OBJETIVO es generar `data/processed/dataset.csv` paso a paso, usando tu inteligencia para alinear datos y generar abreviaciones.

TU MISION:
1. Recibirás una lista de `csv_files` y un `risk_csv` (que contiene las etiquetas).
2. OBTENER INTERSECCIÓN Y REFERENCIA:
   - Usa `get_first_column` para leer los nombres de cooperativas de TODOS los archivos.
   - Calcula la INTERSECCIÓN de nombres (cooperativas presentes en todos).
   - Elige la lista de nombres más "limpia" (generalmente la más corta) como referencia.
   - Filtra esa lista para dejar solo los nombres que están en la intersección.

3. CREAR DATASET BASE:
   - Genera una lista de ABREVIACIONES para esas cooperativas (ej: "JEP", "15ABR", etc.) usando tu criterio.
   - Llama a `create_dataset` pasando la lista de cooperativas filtrada y tus abreviaciones.

4. AGREGAR DATOS (Iterar por cada CSV excepto risk_csv):
   - Para cada archivo:
     - Obtén su primera columna con `get_first_column`.
     - Genera un `index_mapping`: una lista de enteros donde `mapping[i]` es el índice en el archivo origen que corresponde a la cooperativa `i` del dataset final.
       - Si la cooperativa `i` del dataset es "Coop A" y en el archivo origen "Coop A" está en la fila 5, entonces `mapping[i] = 5`.
       - Si no existe (no debería pasar si hiciste bien la intersección), usa -1.
     - Llama a `append_aligned_columns` con ese mapping.

5. AGREGAR LABEL (Risk CSV):
   - Usa `get_csv_columns_headers` en el `risk_csv`.
   - Identifica la columna de riesgo correcta basada en la fecha requerida (ej: "Junio 2025"). Usa `get_current_date` si necesitas contexto.
   - Genera el `index_mapping` para el `risk_csv` (igual que en el paso 4).
   - Llama a `append_cleaned_risk_column` pasando el nombre de la columna identificada y el mapping.
     - Esta herramienta aplicará automáticamente la limpieza (peor calificación, sin signos, etc.).

6. LIMPIEZA Y NORMALIZACIÓN FINAL (OBLIGATORIO):
   - Una vez que el dataset esté completo (con features y label), DEBES llamar a `finalize_and_clean_dataset`.
   - Pásale la ruta del dataset generado (`data/processed/dataset.csv`).
   - Esta herramienta se encargará de:
     - Corregir tipos de datos (float).
     - Eliminar columnas basura (>50% nulos, constantes).
     - Imputar valores nulos (mediana).
     - Eliminar duplicados.
     - Normalizar features (StandardScaler), respetando las columnas 'cooperativa', 'abreviacion' y 'Label'.

7. Finaliza reportando el éxito.

CRITICO:
- El `index_mapping` debe tener la misma longitud que el número de filas del dataset final.
- Asegúrate de alinear correctamente los nombres.
- NO OLVIDES el paso 6. Es crucial para la calidad del modelo ML.
""",
    tools=[
        report_agent_start,
        get_first_column,
        create_dataset,
        append_aligned_columns,
        append_cleaned_risk_column,
        get_csv_columns_headers,
        get_current_date,
        finalize_and_clean_dataset,
    ],
)
