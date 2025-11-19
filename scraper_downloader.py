#### Usando Playwright para descargar datos de la CONSAR
### Especialista en AFORE
### Autor Fernando Dorantes Nieto
# -*- coding: utf-8 -*-
### Fernando Dorantes Nieto
'''
<(*)
  ( >)"
  /|
'''

import os
import sys
import asyncio ## Los métodos asíncronos
import pandas as pd
import os
from playwright.async_api import async_playwright
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


async def descargar_pdfs_consar(dir_to_download_files, existing_df=None):
    #download_dir = "./descargas_consar"
    download_dir = dir_to_download_files
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Prepare a set of already downloaded file identifiers for quick lookup
    # We will use the generated filename as the identifier, e.g., "NOMBRE_0.pdf"
    ### Verificar que el nombre de la path exista
    downloaded_file_names = set()
    if existing_df is not None and not existing_df.empty:
        downloaded_file_names = set(existing_df['archivo_descargado'].dropna().tolist())

    datos = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        print("Navegando a la página...")
        await page.goto('https://www.consar.gob.mx/gobmx/aplicativo/SINORconsar#')
        await page.wait_for_selector('table', timeout=30000)
        print("Tabla detectada, extrayendo datos...")

        filas = await page.query_selector_all('table tbody tr')

        for i, fila in enumerate(filas):
            try:
                celdas = await fila.query_selector_all('td')
                if len(celdas) >= 3:
                    nombre = (await celdas[0].inner_text()).strip()
                    print('Nombre')
                    tipo = (await celdas[1].inner_text()).strip()
                    fecha_dof = (await celdas[2].inner_text()).strip()

                    expected_filename = f"{nombre}_{i}.pdf"
                    ruta_completa = os.path.join(download_dir, expected_filename)

                    # Check if already downloaded and file exists
                    if expected_filename in downloaded_file_names and os.path.exists(ruta_completa):
                        print(f"Saltando: '{nombre}' (ya descargado como '{expected_filename}')")
                        datos.append({
                            'nombre': nombre,
                            'tipo': tipo,
                            'fecha_publicacion_dof': fecha_dof,
                            'archivo_descargado': expected_filename,
                            'ruta_completa': ruta_completa
                        })
                        continue # Skip to next row

                    print(f"Procesando: {nombre}")
                    archivo_descargado = None
                    try:
                        enlace_nombre = await celdas[0].query_selector('a[href*=".pdf"], a[href*="download"]')
                        if enlace_nombre:
                            async with page.expect_download(timeout=60000) as download_info:
                                await enlace_nombre.click()
                                await page.wait_for_timeout(500)
                            download = await download_info.value
                            if download.suggested_filename.lower().endswith('.pdf'):
                                archivo_descargado = expected_filename
                                await download.save_as(ruta_completa)
                                print(f"  ✓ Descargado desde nombre: {archivo_descargado}")

                    except Exception as e:
                        print(f"  ✗ Error descargando desde nombre para '{nombre}': {e}")

                    if not archivo_descargado:
                        try:
                            # Try to find a download button/link more generically in the row
                            boton_descargar = await fila.query_selector('button:has-text("Descargar"), a:has-text("Descargar"), a[href*=".pdf"], a[href*="download"]')
                            if boton_descargar:
                                async with page.expect_download(timeout=60000) as download_info: # Increased timeout
                                    await boton_descargar.click()
                                    await page.wait_for_timeout(500) # Small wait
                                download = await download_info.value
                                if download.suggested_filename.lower().endswith('.pdf'):
                                    archivo_descargado = expected_filename
                                    await download.save_as(ruta_completa)
                                    print(f"  ✓ Descargado desde botón: {archivo_descargado}")

                        except Exception as e:
                            print(f"  ✗ Error descargando desde botón para '{nombre}': {e}")

                    datos.append({
                        'nombre': nombre,
                        'tipo': tipo,
                        'fecha_publicacion_dof': fecha_dof,
                        'archivo_descargado': archivo_descargado,
                        'ruta_completa': ruta_completa if archivo_descargado else None
                    })

            except Exception as e:
                print(f"Error procesando fila {i} ('{nombre if 'nombre' in locals() else 'N/A'}'): {e}")
                continue

        await browser.close()
    return datos, download_dir

def crear_dataframe_y_guardar(datos, download_dir):
    # Crear DataFrame
    df = pd.DataFrame(datos)

    # Guardar DataFrame como CSV
    csv_path = os.path.join(download_dir, "metadata_documentos.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8')

    print(f"\n✅ Proceso completado:")
    print(f"   - Documentos procesados: {len(df)}")
    print(f"   - PDFs descargados: {df['archivo_descargado'].notna().sum()}")
    print(f"   - CSV guardado en: {csv_path}")
    print(f"   - PDFs guardados en: {download_dir}")

    return df

# Función para subir a Google Drive (opcional)
def subir_a_drive(local_folder, drive_folder_id=None):
    """
    Función para subir archivos a Google Drive
    Requiere: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
    """
    try:

        # Configurar autenticación (necesitas configurar las credenciales OAuth 2.0)
        # service = build('drive', 'v3', credentials=creds)

        # Subir archivos
        for filename in os.listdir(local_folder):
            file_path = os.path.join(local_folder, filename)
            if os.path.isfile(file_path):
                file_metadata = {
                    'name': filename,
                    'parents': [drive_folder_id] if drive_folder_id else []
                }
                media = MediaFileUpload(file_path, resumable=True)
                # file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"Subido a Drive: {filename}")

    except ImportError:
        print("Bibliotecas de Google Drive no instaladas. Instala con: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    except Exception as e:
        print(f"Error subiendo a Drive: {e}")