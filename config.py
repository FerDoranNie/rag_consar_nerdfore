### Autor Fernando Dorantes Nieto
# -*- coding: utf-8 -*-
### Fernando Dorantes Nieto
'''
<(*)
  ( >)"
  /|
'''


import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
### Este archivo servirá para ambas versiones
load_dotenv(override=True)

DRIVE_API_KEY = os.getenv('DRIVE_API_KEY')
