import base64
from aiohttp import web
import asyncio
import funciones as fc
import getGP as gp
import argparse
import os
import multiprocessing
from PIL import Image
import ssl
import bottle
bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024
from fast_plate_ocr import ONNXPlateRecognizer
import conexion as conexion
from datetime import datetime,timedelta
import aiofiles
import logging
from tasks import process_image
from marshmallow import Schema, fields, ValidationError
from aiohttp_session import get_session
from concurrent.futures import ProcessPoolExecutor

async def protected_route(request):
    session = await get_session(request)
    if 'user' not in session:
        return web.Response(text='No autorizado', status=403)

logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')

async def home(request):
    
    async with aiofiles.open('index.html', mode='r') as file:
        content = await file.read()

    return web.Response(text=content, content_type='text/html')

async def dashboard(request):
    
    async with aiofiles.open('dashboard.html', mode='r') as file:
        content = await file.read()

    return web.Response(text=content, content_type='text/html')

async def upload(request):
    async with aiofiles.open('upload.html', mode='r') as file:
        content = await file.read()
        
    return web.Response(text=content, content_type='text/html')

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

class CobroSchema(Schema):
    patente = fields.String(required=True)
    tiempo = fields.String(required=True)

async def cobrar(request):
    json_data = await request.post()
    try:
        data = await request.post()
        patente = data['patente']
        tiempo_str = data['tiempo']
        
        tiempo = datetime.fromisoformat(tiempo_str)
        ahora = datetime.now()
        tiempo_transcurrido = ahora - tiempo
        horas, resto = divmod(tiempo_transcurrido.total_seconds(), 3600)
        horas_redondeadas = int(horas) + (1 if resto > 0 else 0)
        
        monto_a_pagar = horas_redondeadas * 500
        
        # Insertar los datos en la tabla cobros
        conexion.insertar_cobro(patente, tiempo_str, monto_a_pagar)
        #conexion.insertar_cobro('ABC123', '2023-06-13T12:34:56', 1000.0)
    except ValidationError as err:
        return web.Response(text=str(err.messages), status=400)    
    return web.Response(text=f'El monto a pagar es: ${monto_a_pagar:.2f}', content_type='text/plain')

executor = ProcessPoolExecutor(max_workers=4)
#concurrent.futures. Este módulo permite ejecutar tareas en múltiples procesos en lugar de hilos, 
# lo cual es útil para tareas que consumen mucho tiempo, como el procesamiento de imágenes, porque puede aprovechar múltiples núcleos del CPU

async def handle_upload(request):
    reader = await request.multipart()
    field = await reader.next()

    # Nombre del archivo
    filename = field.filename

    # Ruta donde se guardará la imagen
    save_path = os.path.join('./images', filename)
    
    try:
        # Guardar la imagen en el servidor de manera asíncrona
        async with aiofiles.open(save_path, 'wb') as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                await f.write(chunk)

        # Agregar la imagen a la cola para procesamiento
        image_queue.put(save_path)
        
        # Enviar la tarea a Celery
        #task = process_image.delay(save_path)
        
        result_path = image_queue.get()
        await loop.run_in_executor(executor, patente_worker, save_path)
        return web.Response(text=f'Imagen "{filename}" cargada con éxito.', content_type='text/plain')
    
    except Exception as e:
        return web.Response(text=f'Error al guardar la imagen: {str(e)}', status=500)
    
    
async def handle_pagar(request):
    reader = await request.multipart()
    field = await reader.next()

    # Nombre del archivo
    filename = field.filename

    # Ruta donde se guardará la imagen 
    save_path = os.path.join('./images', filename)

    # Guardar la imagen en el servidor
    with open(save_path, 'wb') as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            f.write(chunk)
    
    # Agregar la imagen a la cola para procesamiento 
    image_queue.put(save_path)

    # Bloquear hasta que la conversión de la imagen esté completa
    result_path = image_queue.get()

    return web.Response(text=f'Imagen "{filename}" cargada con éxito.', content_type='text/plain')

async def get_dashboard_data(request):
    try:
        datos = conexion.obtener_datos()  # Implementa esta función en tu módulo de conexión
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

async def patente_worker(queue):
    while True:
        try:
            image_path = queue.get()
            if image_path is None:
                break

            # Procesar la imagen
            m = ONNXPlateRecognizer('argentinian-plates-cnn-model')
            nropatente = m.run(image_path)
            print(nropatente, type(nropatente))
            
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()

            link = gp.convert_to_gplink(image_path)
            print("La ubicación es:", link)

            # Insertar en la base de datos
            conexion.insert_en_tabla(image_path, nropatente, link)
            
            # Generar la ruta de la imagen validada
            asignada_image_path = os.path.join('./Validada', 'validada_' + os.path.basename(image_path))
            # Agregar la imagen convertida a la cola de resultados
            image_queue.put(asignada_image_path)

        except Exception as e:
            # Loguear el error
            print(f"Error en el procesamiento de la imagen {image_path}: {e}")
            # Enviar mensaje de error o realizar otras acciones según sea necesario

        


def list_images(folder_path, allowed_formats=None):
    
    image_list = []

    # Si no se especifican formatos permitidos, se aceptan todos
    if allowed_formats is None:
        allowed_formats = [".jpg", ".jpeg", ".png", ".gif", ".bmp","dng"]

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
@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    except Exception as e:
        logging.error(f"Error procesando la solicitud: {str(e)}")
        return web.Response(text='Error interno del servidor.', status=500)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Arrays')
    parser.add_argument('-p', '--port', required=True,action="store", dest="puerto",type=int, help="Puerto")
    
    args = parser.parse_args()
    puerto=args.puerto
    
    image_queue = multiprocessing.Queue()

    # Crear el proceso hijo para el servicio 
    patente_process = multiprocessing.Process(target=patente_worker, args=(image_queue,))
    patente_process.start()

    app = web.Application()
    app.router.add_get('/', home)
    app.router.add_get('/upload.html', upload)
    app.router.add_post('/upload', handle_upload)
    app.router.add_post('/pagar', handle_pagar)
    app.router.add_post('/cobrar', cobrar)
    app.router.add_get('/show.html', show)
    app.router.add_get('/api/dashboard-data', get_dashboard_data)
    app.middlewares.append(error_middleware)
        
    #app.router.add_static('/static/', path='./static', name='static')

    # Configuración de SSL para habilitar HTTPS
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain('./certs/cert.pem', './certs/key.pem')

    runner = web.AppRunner(app)

    # Configurar el bucle de eventos
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())

    #site = web.TCPSite(runner, '0.0.0.0', puerto,ssl_context=ssl_context) ver este tema
    # Permitir conexiones en IPv4
    site_ipv4 = web.TCPSite(runner, '0.0.0.0', puerto,ssl_context=ssl_context)
    loop.run_until_complete(site_ipv4.start())
    
    # Permitir conexiones en IPv6
    site_ipv6 = web.TCPSite(runner, '::', puerto, ssl_context=ssl_context)
    loop.run_until_complete(site_ipv6.start())

    print("Servidor web en ejecución en https://0.0.0.0:",puerto)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Detener el servicio de escala de grises
        image_queue.put(None)
        patente_process.join()

        # Limpiar el bucle de eventos
        loop.run_until_complete(runner.cleanup())

        # Cerrar el bucle de eventos
        loop.stop()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        
        # Detener sitios IPv4 e IPv6
        loop.run_until_complete(site_ipv4.stop())
        loop.run_until_complete(site_ipv6.stop())
