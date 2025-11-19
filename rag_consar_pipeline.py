### Script principal o el main
### Autor Fernando Dorantes Nieto
# -*- coding: utf-8 -*-
### Fernando Dorantes Nieto
'''
<(*)
  ( >)"
  /|
'''
import os
import json
import shutil
import logging
from docling.document_converter import DocumentConverter

from general_functions import get_file_category, get_current_timestamp_utc
from convert_audio_videos_files_to_simple_text import (
    transcribe_audio_file,
    transcribe_video_to_audio_to_text
)
from image_to_text import extract_text_from_image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def convertDocument(filename_string):
    """
    Convierte un documento (como .docx, .pdf) a formato Markdown.

    Args:
        filename_string (str): La ruta al archivo del documento.
    """
    converter = DocumentConverter()
    doc = converter.convert(filename_string).document
    md=  doc.export_to_markdown()
    return md 







def process_file_to_text(file_path: str) -> str | None:
    """
    Procesa un archivo para extraer su contenido de texto basado en su tipo.

    Args:
        file_path (str): La ruta al archivo a procesar.

    Returns:
        str | None: El texto extraído del archivo, o None si falla la extracción.
    """
    category = get_file_category(file_path)
    filename = os.path.basename(file_path)
    logging.info(f"Procesando archivo '{filename}' en la categoría: {category}")

    try:
        if category == "audio":
            return transcribe_audio_file(file_path)
        elif category == "video":
            return transcribe_video_to_audio_to_text(file_path)
        elif category == "texto":
            # convertDocument maneja .docx, .pdf, .pptx, etc.
            return convertDocument(file_path)
        elif category == "imagen":
            return extract_text_from_image(file_path, language='spa')
        else:
            logging.warning(f"Categoría de archivo '{category}' no soportada para '{filename}'.")
            return None
    except Exception as e:
        logging.error(f"Error al procesar el archivo '{filename}': {e}")
        return None


def pipeline_consar(file_path: str) -> str | None:
    """
    Función principal que toma la ruta de un archivo, detecta su tipo,
    lo convierte a texto simple y devuelve el resultado.

    Args:
        file_path (str): La ruta completa al archivo a procesar. 

    Returns:
        str: El contenido del archivo como texto simple si la conversión es exitosa.
             Si la conversión falla, devuelve la ruta original del archivo (`file_path`).
             Devuelve `None` solo si el archivo de entrada no existe.
    """
    if not os.path.exists(file_path):
        logging.error(f"El archivo no fue encontrado: {file_path}")
        return None
    
    logging.info(f"Iniciando pipeline para el archivo: {os.path.basename(file_path)}")
    extracted_text = process_file_to_text(file_path)
    
    if extracted_text:
        logging.info(f"Pipeline completado. Se extrajo texto del archivo.")
        return extracted_text
    else:
        logging.warning(f"No se pudo extraer texto del archivo '{os.path.basename(file_path)}'. Devolviendo la ruta original.")
        return file_path


def process_folder_and_move_files(input_folder: str, success_folder: str, failed_folder: str, output_format: str = 'json'):
    """
    Procesa archivos de una carpeta. Los exitosos se guardan en la carpeta de éxito
    y los fallidos se mueven a la carpeta de fallos.

    Args:
        input_folder (str): La carpeta con los archivos originales.
        success_folder (str): Carpeta para guardar los resultados de conversiones exitosas.
        failed_folder (str): La carpeta donde se moverán los archivos que no se pudieron convertir.
        output_format (str, optional): El formato del archivo de salida para las conversiones
                                       exitosas. Puede ser 'json' o 'txt'. 
                                       Por defecto es 'json'.
    """
    os.makedirs(success_folder, exist_ok=True)
    os.makedirs(failed_folder, exist_ok=True)

    if output_format not in ['json', 'txt']:
        logging.error("Formato de salida no válido. Debe ser 'json' o 'txt'.")
        return

    if not os.path.isdir(input_folder):
        logging.error(f"La carpeta de entrada no existe: {input_folder}")
        return

    logging.info(f"Iniciando procesamiento de la carpeta: {input_folder}")
    
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if not os.path.isfile(file_path):
            continue

        result = pipeline_consar(file_path)

        # Comprobamos si el resultado es el texto extraído o la ruta del archivo original
        if result and result != file_path:
            base_filename, _ = os.path.splitext(filename)

            if output_format == 'json':
                # --- ÉXITO: Guardar como JSON ---
                record = {
                    "source_file": filename,
                    "processed_at_utc": get_current_timestamp_utc(),
                    "text": result
                }
                output_path = os.path.join(success_folder, f"{base_filename}.json")
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(record, f, ensure_ascii=False, indent=4)
                    logging.info(f"Éxito: '{filename}' -> Guardado como JSON en '{output_path}'")
                except Exception as e:
                    logging.error(f"Error al guardar el archivo JSON '{output_path}': {e}")
            
            elif output_format == 'txt':
                # --- ÉXITO: Guardar como TXT ---
                output_path = os.path.join(success_folder, f"{base_filename}.txt")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result)
                logging.info(f"Éxito: '{filename}' -> Guardado como TXT en '{output_path}'")
        else:
            # --- FALLO: El resultado es la ruta del archivo o None ---
            failed_path = os.path.join(failed_folder, filename)
            try:
                shutil.move(file_path, failed_path)
                logging.warning(f"Fallo: '{filename}' -> Movido a '{failed_path}'")
            except Exception as e:
                logging.error(f"Error al mover el archivo fallido '{filename}': {e}")

    logging.info("Procesamiento de la carpeta completado.")


if __name__ == '__main__':
    # --- Ejemplo de uso con la nueva función orquestadora ---
    
    # 1. Define tus carpetas
    INPUT_DIR = "C:/ruta/a/tus/archivos_de_entrada"
    SUCCESS_DIR = "C:/ruta/a/tus/archivos_convertidos"
    FAILED_DIR = "C:/ruta/a/tus/archivos_fallidos"

    # 2. Llama a la función principal eligiendo el formato de salida.
    
    # Para generar archivos .json (opción por defecto)
    process_folder_and_move_files(INPUT_DIR, SUCCESS_DIR, FAILED_DIR, output_format='json')

    # Para generar archivos .txt
    # process_folder_and_move_files(INPUT_DIR, SUCCESS_DIR, FAILED_DIR, output_format='txt')
