#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import base64
import conexion as conexion
from datetime import datetime,timedelta
from aiohttp import web
from concurrent import futures
from PIL import Image

_ERROR_ARCHIVO = "El archivo no se encuentra en el directorio"


async def show(request):
    
    datos = conexion.obtener_datos()
    
    # Obtener la fecha y hora actual
    ahora = datetime.now()
    
    # Construir el contenido HTML
    contenido_html = """
    <html>
    <head>
        <title>Datos de la tabla Patente</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.4.1/dist/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
        <style>
            img { max-width: 200px; max-height: 200px; }
            .rojo { color: red; }
            .modal {
                display: none;
                position: fixed;
                z-index: 1;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                overflow: auto;
                background-color: rgb(0,0,0);
                background-color: rgba(0,0,0,0.4);
                padding-top: 60px;
            }
            .modal-content {
                background-color: #fefefe;
                margin: 5% auto;
                padding: 20px;
                border: 1px solid #888;
                width: 80%;
            }
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
            }
            .close:hover,
            .close:focus {
                color: black;
                text-decoration: none;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>Datos de la tabla Patente</h1>
        <table class='table table-dark' border='1'>
            <tr>
                <th>Fecha y Hora</th>
                <th>Imagen</th>
                <th>Ubicación</th>
                <th>Patente</th>
                <th>Tiempo Transcurrido</th>
                <th></th>
            </tr>
    """
    
    for fila in datos:
        fecha_hora = fila[1].strftime("%Y-%m-%d %H:%M")  # Formatear fecha y hora
        imagen_base64 = base64.b64encode(fila[2]).decode('utf-8')
        ubicacion = fila[3]
        
        # Calcular el tiempo transcurrido
        tiempo_transcurrido = ahora - fila[1]
        horas, resto = divmod(tiempo_transcurrido.total_seconds(), 3600)
        minutos = resto // 60
        tiempo_transcurrido_formateado = f"{int(horas)} horas, {int(minutos)} minutos"
        
        # Redondear hacia arriba el tiempo en horas
        horas_redondeadas = int(horas) + (1 if minutos > 0 else 0)
        
        # Verificar si el tiempo transcurrido es mayor a una hora
        if tiempo_transcurrido > timedelta(hours=1):
            estilo_tiempo_transcurrido = 'rojo'
            boton_cobrar = f"""
                <form onsubmit="event.preventDefault(); cobrar('{fila[4]}', '{fila[1].isoformat()}');">
                    <button type='submit'>Cobrar</button>
                </form>
            """
        else:
            estilo_tiempo_transcurrido = ''
            boton_cobrar = ''
        
        # Modificación para hacer que la ubicación sea un enlace
        contenido_html += f"""
            <tr>
                <td>{fecha_hora}</td>
                <td><img src='data:image/jpeg;base64,{imagen_base64}' alt='Imagen'></td>
                <td><a href='{ubicacion}' target='_blank'>{ubicacion}</a></td>
                <td>{fila[4]}</td>
                <td class='{estilo_tiempo_transcurrido}'>{tiempo_transcurrido_formateado}</td>
                <td>{boton_cobrar}</td>
            </tr>
        """
    
    contenido_html += """
        </table>

        <div id="myModal" class="modal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <p id="modal-text"></p>
            </div>
        </div>

        <script>
            async function cobrar(patente, tiempo) {
                const response = await fetch('/cobrar', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: `patente=${patente}&tiempo=${tiempo}`
                });

                const result = await response.text();
                document.getElementById('modal-text').innerText = result;
                document.getElementById('myModal').style.display = 'block';
            }

            var modal = document.getElementById("myModal");
            var span = document.getElementsByClassName("close")[0];

            span.onclick = function() {
                modal.style.display = "none";
            }

            window.onclick = function(event) {
                if (event.target == modal) {
                    modal.style.display = "none";
                }
            }
        </script>
    </body>
    </html>
    """

    return web.Response(text=contenido_html, content_type='text/html')

async def get_dashboard_data(request):
    try:
        datos = conexion.obtener_datos() 
        data_list = []
        for fila in datos:
            data_list.append({
                'fecha_hora': fila[1].strftime('%Y-%m-%d %H:%M'),
                'imagen': base64.b64encode(fila[2]).decode('utf-8'),
                'ubicacion': fila[3],
                'patente': fila[4],
                'tiempo_transcurrido': str(datetime.now() - fila[1])
            })
        return web.json_response(data_list)
    except Exception as e:
        return web.json_response({'error': str(e)})
    
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
validate_images_folder = './images'
validate_image_list = list_images(validate_images_folder)
