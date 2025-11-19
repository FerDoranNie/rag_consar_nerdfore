import os
import whisper
from pydub import AudioSegment
import speech_recognition as sr
import logging
import pandas as pd
import numpy as np

from video_to_audio import video_to_audio
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Cargando modelo de Whisper 'medium'...")
whisperModel = whisper.load_model('medium')
logging.info("Modelo de Whisper cargado exitosamente.")

def transcribe_audio_array(audio_array: np.ndarray, language: str = "es") -> tuple[str, pd.DataFrame] | None:
    if not isinstance(audio_array, np.ndarray):
        logging.error("La entrada no es un array de NumPy válido.")
        return None
    try:
        logging.info(f"Iniciando transcripción en idioma '{language}'...")
        # El array ya está en el formato que Whisper espera (float32)
        result = whisperModel.transcribe(audio_array, language=language)
        
        transcribed_text = result['text']        
        logging.info("Transcripción completada exitosamente.")
        return transcribed_text
    except Exception as e:
        logging.error(f"Error durante la transcripción con Whisper: {e}")
        return None


def transcribe_audio_file(audio_path: str, language: str = "es") -> str | None:
    if not os.path.exists(audio_path):
        logging.error(f"El archivo de audio no fue encontrado en la ruta: {audio_path}")
        return None

    try:
        logging.info(f"Iniciando transcripción del archivo '{os.path.basename(audio_path)}' en idioma '{language}'...")
        # Whisper puede procesar la ruta del archivo directamente
        result = whisperModel.transcribe(audio_path, language=language)
        transcribed_text = result['text']
        logging.info(f"Transcripción del archivo '{os.path.basename(audio_path)}' completada exitosamente.")
        return transcribed_text
    except Exception as e:
        logging.error(f"Error durante la transcripción del archivo '{audio_path}': {e}")
        return None



def transcribe_video_to_audio_to_text(video_path, language='es'):
    try:
        print('Creando archivo temporal')
        video_to_audio(video_path, 'temp.wav')
        audio_path = 'temp.wav'
        text_from_audio = transcribe_audio_file(audio_path=audio_path, language=language)
        print('Borrando archivo temporal')
        if os.path.isfile(audio_path):
            os.remove(audio_path)
        return text_from_audio
    except Exception as e: 
        logging.error(f"Error durante la transcripción del archivo '{video_path}': {e}")
        return None 


#### Funciones de video a audio
from moviepy import VideoFileClip
import logging
import numpy as np
from io import BytesIO
from typing import Optional
from scipy.io.wavfile import write as write_wav
 
# Configurar logging para mostrar mensajes informativos y de error
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def video_to_audio(video_path: str, audio_path: str) -> str | None:
    """
    Extrae el audio de un archivo de video y lo guarda en la ruta especificada.

    Args:
        video_path (str): La ruta al archivo de video de entrada.
        audio_path (str): La ruta donde se guardará el archivo de audio extraído (ej. 'output.mp3').

    Returns:
        Optional[str]: La ruta al archivo de audio creado si la conversión es exitosa, 
                    en caso contrario, None.
    """
    video_clip = None
    try:
        logging.info(f"Iniciando extracción de audio para: {video_path}")
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        
        # Escribir el archivo de audio. Moviepy deducirá el códec del nombre del archivo.
        audio_clip.write_audiofile(audio_path)
        
        logging.info(f"Audio guardado exitosamente en: {audio_path}")
        return audio_path
    except Exception as e:
        logging.error(f"Error al convertir el video a audio para '{video_path}': {e}")
        return None
    finally:
        # Asegurarse de cerrar los clips para liberar recursos
        if video_clip and video_clip.audio:
            audio_clip.close()
        if video_clip:
            video_clip.close()


def extract_audio_for_transcription(video_path: str) -> np.ndarray | None:
    """
    Extrae el audio de un video y lo devuelve como un array NumPy,
    listo para ser procesado por modelos como Whisper.

    El audio se convierte a mono y se remuestrea a 16kHz.

    Args:
        video_path (str): La ruta al archivo de video de entrada.

    Returns:
        Optional[np.ndarray]: Un array NumPy con la forma de onda del audio si es exitoso,
                          en caso contrario, None.
    """
    video_clip = None
    audio_clip = None
    try:
        logging.info(f"Extrayendo audio en memoria desde: {video_path}")
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio

        # Convertir el audio a un array NumPy, remuestreando a 16kHz (estándar para Whisper)
        # El resultado es un array flotante, que es lo que Whisper espera.
        audio_waveform = audio_clip.to_soundarray(fps=16000)

        # Asegurarse de que el audio sea mono (un solo canal)
        if audio_waveform.ndim > 1 and audio_waveform.shape[1] == 2:
            audio_waveform = audio_waveform.mean(axis=1) 

        logging.info(f"Audio extraído en memoria exitosamente.")
        return audio_waveform.astype(np.float32)
    except Exception as e:
        logging.error(f"Error al extraer el audio en memoria para '{video_path}': {e}")
        return None
    finally:
        if audio_clip:
            audio_clip.close()
        if video_clip:
            video_clip.close()


def video_to_audio_buffer(video_path: str) -> Optional[BytesIO]:
    """
    Extrae el audio de un video y lo guarda en un buffer en memoria como formato WAV.

    Este buffer es ideal para ser consumido directamente por librerías de transcripción
    como Whisper, evitando la creación de archivos temporales en disco.

    Args:
        video_path (str): La ruta al archivo de video de entrada.

    Returns:
        Optional[BytesIO]: Un objeto BytesIO con el audio en formato WAV si es exitoso,
                           en caso contrario, None.
    """
    video_clip = None
    audio_clip = None
    try:
        logging.info(f"Iniciando extracción de audio a buffer desde: {video_path}")
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio

        audio_buffer = BytesIO()
        # 1. Extraer la forma de onda del audio a 16kHz.
        audio_waveform = audio_clip.to_soundarray(fps=16000)

        # 2. Asegurarse de que el audio sea mono.
        if audio_waveform.ndim > 1 and audio_waveform.shape[1] == 2:
            audio_waveform = audio_waveform.mean(axis=1)

        # 3. Convertir la forma de onda de float a int16, que es el formato estándar para WAV (pcm_s16le).
        # Whisper internamente maneja float32, pero para un archivo WAV estándar, int16 es más común.
        # Multiplicamos por el valor máximo de int16 para escalar la señal.
        audio_int16 = (audio_waveform * 32767).astype(np.int16)

        # 4. Escribir el array NumPy en el buffer en formato WAV usando SciPy.
        write_wav(audio_buffer, 16000, audio_int16)

        # Regresar el cursor al inicio del buffer para que pueda ser leído
        audio_buffer.seek(0)
        
        logging.info("Audio extraído a buffer en memoria exitosamente.")
        return audio_buffer
    except Exception as e:
        logging.error(f"Error al convertir el video a buffer de audio para '{video_path}': {e}")
        return None
    finally:
        if audio_clip:
            audio_clip.close()
        if video_clip:
            video_clip.close()
