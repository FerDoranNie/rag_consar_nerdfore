### Autor Fernando Dorantes Nieto
# -*- coding: utf-8 -*-
import pytesseract
from PIL import Image
import logging
import os

# --- CONFIGURACIÓN DE TESSERACT ---
# Si instalaste Tesseract en una ubicación no estándar, o si no lo agregaste al PATH,
# descomenta la siguiente línea y ajusta la ruta a tu ejecutable tesseract.exe.
# Por ejemplo, en una instalación típica de Windows:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_text_from_image(image_path: str, language: str = 'spa') -> str | None:
    """
    Extrae texto de un archivo de imagen utilizando Tesseract OCR.

    Args:
        image_path (str): La ruta al archivo de imagen.
        language (str): El código de idioma para Tesseract (ej. 'eng' para inglés, 'spa' para español).

    Returns:
        str | None: El texto extraído de la imagen, o None si ocurre un error.
    """
    if not os.path.exists(image_path):
        logging.error(f"El archivo de imagen no fue encontrado: {image_path}")
        return None

    try:
        logging.info(f"Iniciando extracción de texto (OCR) para la imagen: {os.path.basename(image_path)}")
        # Usamos Pillow (PIL) para abrir la imagen y pytesseract para extraer el texto
        text = pytesseract.image_to_string(Image.open(image_path), lang=language)
        logging.info("Extracción de texto de la imagen completada.")
        return text.strip()
    except Exception as e:
        logging.error(f"Error durante el OCR en el archivo '{image_path}': {e}")
        return None