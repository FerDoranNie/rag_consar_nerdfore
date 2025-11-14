import sys 
import os 
import unicodedata
import re 

## Función para remover acentos

def remove_accents(input_str):
    if not isinstance(input_str, str):
        raise TypeError("Input must be a string.")
    normalized = unicodedata.normalize('NFD', input_str)

    without_accents = ''.join(
        char for char in normalized
        if unicodedata.category(char) != 'Mn'
    )
    return without_accents


def clean_string(string_to_clean, with_underscore=False):
  string_cleaned = re.sub(r'_', ' ', string_to_clean)
  ## Cambiar acentos por letras sin acentos, también aplica la ñ
  string_cleaned = remove_accents(string_cleaned)
  ## Remover caracteres raros
  string_cleaned = re.sub(r'[^\w\s]', '', string_cleaned)
  ## Convert to UTF8
  string_cleaned = string_cleaned.encode('utf-8').decode('utf-8')
  string_cleaned = re.sub(r'\s+', ' ', string_cleaned)
  ### Remover espacios al inicio y al final
  string_cleaned = string_cleaned.strip()
  if with_underscore:
    return  string_cleaned.replace(' ', '_').lower()
  else:
    return string_cleaned.lower()
