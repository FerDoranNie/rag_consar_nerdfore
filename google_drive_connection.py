import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.auth.transport.requests import Request
import os
from config import DRIVE_API_KEY, SCOPES, CREDENTIALS_FILE

TOKEN_FILE = NULL

def authenticate_gdrive():
    """
    Maneja la autenticación con Google Drive para persistencia.
    Usa token.json si existe, o inicia el flujo OAuth2.
    """
    creds = None

    # 1. Cargar credenciales desde token.json
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 2. Refrescar o (re)autenticar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refrescar token expirado
            logging.info("Token expirado. Refrescando...")
            creds.refresh(Request())
        else:
            # Autenticación inicial o token no encontrado
            if not os.path.exists(CREDENTIALS_FILE):
                logging.error(f"Error: El archivo de credenciales no se encontró en: {CREDENTIALS_FILE}")
                return None

            logging.info("Iniciando flujo de autenticación OAuth2...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Nota: Usa run_local_server para desarrollo interactivo con navegador
            creds = flow.run_local_server(port=8080)

        # 3. Guardar el nuevo token
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            logging.info(f"Token actualizado y guardado exitosamente en {TOKEN_FILE}")

    try:
        service = build('drive', 'v3', credentials=creds)
        logging.info("Servicio de Google Drive autenticado correctamente.")
        return service
    except Exception as e:
        logging.error(f"Error al construir el servicio de Google Drive: {e}")
        return None


