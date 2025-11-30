import os
from agents import Agent, Runner, function_tool
from tools.shared import report_agent_start
from tools.shared import log
from tools.formats.pdf import (
    extract_text_from_pdf,
    file_to_base64,
    save_csv_from_pdf,
    update_csv_with_correction
)
from custom_agents.consolidator.extractors.pdf.pdf_cleaner import pdf_cleaner

pdf_extractor = Agent(
    name="Pdf Extractor",
    model="gpt-5",
    instructions="""
    Eres un agente experto en extracción de datos de documentos PDF.
    PRIMERO: Llama a `report_agent_start` con tu nombre y una descripción corta.
    Tu tarea es recibir un archivo PDF, encontrar la tabla de datos financieros o de riesgo de cooperativas, y extraerla COMPLETAMENTE (si esta separada en paginas juntala, pero tienes que extraer TODA la tabla) y EXACTAMENTE como está.
    Asegurate que cada celda caudre con el lugar de la tabla en el que estaba en el pdf, no deberia haber celdas sin datos (pero NO te puedes inventar ninguno), ni deben haber datos en lugares en donde no hay headers por ejemplo (tipo fuera de la estructura principal de la tabla).
    Si se trata de una valoracion de riesgos asegurate de obtener todos los valores de riesgos y exactamente donde deberian estar en la tabla.
    
    FLUJO DE TRABAJO:
    1. Analiza el archivo PDF adjunto visualmente.
    2. Extrae la tabla completa en formato CSV y guárdala usando `save_csv_from_pdf`.
    3. VERIFICACIÓN Y CORRECCIÓN (OBLIGATORIO):
       - Una vez guardado el CSV inicial, llama a `extract_text_from_pdf` para obtener el texto crudo del archivo.
       - Compara el texto extraído con los datos de tu CSV.
       - Busca discrepancias en valores numéricos o valores de riesgos (ej: AA-, numeros, etc).
       - Si encuentras discrepancias en esos valores deterministicos, CORRIGE el contenido CSV y guárdalo usando `update_csv_with_correction`.
       - PERO RECUERDA, EL CSV INCIAL ES EL QUE DEBE TENER MAS VALIDEZ, Y SU ESTRUCTURA NO LA CAMBIES PARA NADA, SOLO HAY QUE COMPARAR VALORES Y CAMBIAR SI NO LOS DETERMINASTE BIEN PORQUE CON EL TEXTO EXTRAIDO EL VALOR SI O SI ES ESE. 
    4. LIMPIEZA FINAL (OBLIGATORIO):
       - Llama al agente `clean_csvs` pasando la ruta COMPLETA del archivo CSV generado (ej: `data/preprocessed/riesgo_2025.csv`) y el `target_segment` si se te proporcionó.
       - Esto estandarizará las columnas y filtrará filas si es necesario.
    
    El usuario te proporcionará el nombre del archivo de salida y opcionalmente el `target_segment` en el prompt.
    """,
    tools=[
        report_agent_start,
        save_csv_from_pdf, 
        extract_text_from_pdf, 
        update_csv_with_correction,
        pdf_cleaner.as_tool(
            tool_name="clean_csvs",
            tool_description="Limpia y estandariza un archivo CSV específico, filtrando por segmento si es necesario.",
            max_turns=15
        )
    ]
)

@function_tool
async def process_pdf(file_path: str, output_filename: str, target_segment: str = None) -> str:
    """
    Procesa un archivo PDF para extraer tablas y guardarlas como CSV.
    
    Args:
        file_path: Ruta al archivo PDF (ej: 'data/preprocessed/archivo.pdf').
        output_filename: Nombre del archivo CSV de salida (ej: 'riesgo_junio_2025.csv').
        target_segment: (Opcional) Segmento específico a filtrar (ej: "1").
    """
    log(f"📄 Procesando PDF: {file_path} (Segmento: {target_segment})")
    
    if not os.path.exists(file_path):
        return f"Error: El archivo {file_path} no existe."
        
    try:
        b64_file = file_to_base64(file_path)
        
        prompt = f"Extrae la tabla de este PDF y guárdala como '{output_filename}'. Luego verifica el texto con extract_text_from_pdf('{file_path}') y corrige si es necesario."
        if target_segment:
            prompt += f" Finalmente, usa clean_csvs pasando el archivo 'data/preprocessed/{output_filename}' y target_segment='{target_segment}'."
        else:
            prompt += f" Finalmente, usa clean_csvs pasando el archivo 'data/preprocessed/{output_filename}'."

        # Mensaje inicial con el archivo y la instrucción
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_data": f"data:application/pdf;base64,{b64_file}",
                        "filename": os.path.basename(file_path),
                    }
                ],
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Ejecutar el agente
        result = await Runner.run(
            starting_agent=pdf_extractor,
            input=messages,
            max_turns=15
        )
        
        print(f"Procesamiento de PDF completado. Resultado: {result.final_output}")
        
        return f"Procesamiento de PDF completado. Resultado: {result.final_output}"
        
    except Exception as e:
        print(f"Error procesando PDF: {str(e)}")
        return f"Error procesando PDF: {str(e)}"
