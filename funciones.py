#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sys 
import binascii
import fnmatch
import re
import PIL

from concurrent import futures
from PIL import Image
import array

_ERROR_ARCHIVO = "El archivo no se encuentra en el directorio"

def abrir_archivo(file):
    '''Abre el archivo indicado en modo lectura'''
    try :
        fd = os.open(file, os.O_RDONLY)
        return fd
    except FileNotFoundError:
        return 0
    
def crear_archivo(file):
    '''Crea el archivo indicado en modo escritura'''
    fd = os.open(file, os.O_WRONLY | os.O_CREAT)
    return fd

def remove_lead_and_trail_slash(s):
    if s.startswith('/'):
        s = s[1:]
    if s.endswith('/'):
        s = s[:-1]
    return s

def list_images(folder_path, allowed_formats=None):
    
    image_list = []

    # Si no se especifican formatos permitidos, se aceptan todos
    if allowed_formats is None:
        allowed_formats = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]

    # Obtener la lista de archivos en la carpeta especificada
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Verificar si el archivo es una imagen válida
        try:
            with Image.open(file_path):
                # Verificar si la extensión del archivo está en los formatos permitidos
                if any(filename.lower().endswith(format) for format in allowed_formats):
                    image_list.append(filename)
        except (IOError, OSError):
            pass  # El archivo no es una imagen válida

    return image_list

# Uso específico para la carpeta Grayscale
validate_images_folder = './Validada'
validate_image_list = list_images(validate_images_folder)
