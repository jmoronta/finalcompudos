import base64
from aiohttp import web
import asyncio
import funciones as fc
import getGP as gp
import argparse
import os
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

image_queue = asyncio.Queue()

result_queue = asyncio.Queue()

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
        await conexion.insertar_cobro(patente, tiempo_str, monto_a_pagar)
        #conexion.insertar_cobro('ABC123', '2023-06-13T12:34:56', 1000.0)
    except ValidationError as err:
        return web.Response(text=str(err.messages), status=400)    
    return web.Response(text=f'El monto a pagar es: ${monto_a_pagar:.2f}', content_type='text/plain')

async def handle_upload(request):
    reader = await request.multipart()
    field = await reader.next()

    filename = field.filename
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
        await image_queue.put(save_path)

        # Responder con una página HTML que incluya el mensaje y el botón
        response_text = f"""
        <html>
        <head>
            <title>Carga Exitosa</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin-top: 50px;
                }}
                .button {{
                    padding: 10px 20px;
                    font-size: 16px;
                    color: white;
                    background-color: #007bff;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    text-decoration: none;
                }}
                .button:hover {{
                    background-color: #0056b3;
                }}
            </style>
        </head>
        <body>
            <h1>Imagen "{filename}" cargada con éxito.</h1>
            <p>¡Gracias por subir la imagen!</p>
            <a href="/" class="button">Volver al inicio</a>
        </body>
        </html>
        """
        
        return web.Response(text=response_text, content_type='text/html')

        
    except Exception as e:
        return web.Response(text=f'Error al guardar la imagen: {str(e)}', status=500)

async def wait_for_result(response):
    # Espera un mensaje de la cola de resultados
    result_message = await result_queue.get()
    print(f"Resultado recibido: {result_message}")

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
    await result_queue.get()

    return web.Response(text=f'Imagen "{filename}" cargada con éxito.', content_type='text/plain')

executor = ProcessPoolExecutor(max_workers=4)
#concurrent.futures. Este módulo permite ejecutar tareas en múltiples procesos en lugar de hilos, 
# lo cual es útil para tareas que consumen mucho tiempo, como el procesamiento de imágenes, porque puede aprovechar múltiples núcleos del CPU

async def patente_worker(queue):
    while True:
        try:
            image_path = await queue.get()
            if image_path is None:
                print("Terminando el worker...")
                break
            
            print(f"Procesando imagen en: {image_path}")
            
            # Procesar la imagen
            m = ONNXPlateRecognizer('argentinian-plates-cnn-model')
            nropatente = m.run(image_path)
            print(nropatente, type(nropatente))
            
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()

            # Delegar el procesamiento de la imagen al executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, process_image, image_path)
            #La llamada se "espera" de manera asincrónica, permitiendo que el bucle de eventos siga ejecutando otras tareas mientras el procesamiento de la imagen ocurre en paralelo
            #Evita bloquear el bucle de eventos principal mientras
            
            # Procesar el resultado obtenido
            patente, link, imagen_procesada = result
            print(f"Patente detectada: {patente}, Link generado: {link}")
            
            # Insertar en la base de datos
            conexion.insert_en_tabla(image_path, nropatente, link)
            
            await result_queue.put("Procesamiento completado")
            
            # Generar la ruta de la imagen validada
            asignada_image_path = os.path.join('./images', 'validada_' + os.path.basename(image_path))
            # Agregar la imagen convertida a la cola de resultados
            #await image_queue.put(image_path)

        except Exception as e:
            # Loguear el error
            print(f"Error en el procesamiento de la imagen {image_path}: {e}")
            # Enviar mensaje de error o realizar otras acciones según sea necesario

# Función intensiva de CPU que será ejecutada por el executor
def process_image(image_path):
    try:
        m = ONNXPlateRecognizer('argentinian-plates-cnn-model')
        nropatente = m.run(image_path)

        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        # Intentar obtener el link
        link = gp.convert_to_gplink(image_path)

        return nropatente, link, image_data
    except Exception as e:
        print(f"Error en process_image: {e}")
        raise

# Lanza la función asincrónica utilizando asyncio
async def start_patente_worker(queue):
    # Usamos asyncio.create_task para ejecutar patente_worker en paralelo
    return asyncio.create_task(patente_worker(queue))        


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

# Captura excepciones y devuelve un mensaje de error al usuario.
@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    except Exception as e:
        logging.error(f"Error procesando la solicitud: {str(e)}")
        return web.Response(text='Error interno del servidor.', status=500)

# Función principal asincrónica para iniciar el servidor y el worker
async def main():    
    parser = argparse.ArgumentParser(description='Arrays')
    parser.add_argument('-p', '--port', required=True,action="store", dest="puerto",type=int, help="Puerto")
    
    args = parser.parse_args()
    puerto=args.puerto
    
    asyncio.create_task(start_patente_worker(image_queue)) #creamos la cola de mensajes

    # Configuración del servidor web con aiohttp
    app = web.Application()
    app.router.add_get('/', home)
    app.router.add_get('/upload.html', upload)
    app.router.add_post('/upload', handle_upload)
    app.router.add_post('/pagar', handle_pagar)
    app.router.add_post('/cobrar', cobrar)
    app.router.add_get('/show.html', fc.show)
    app.router.add_get('/api/dashboard-data', fc.get_dashboard_data)
    app.middlewares.append(error_middleware)
        
    #app.router.add_static('/static/', path='./static', name='static')

    # Configuración de SSL para habilitar HTTPS
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain('./certs/cert.pem', './certs/key.pem')

    runner = web.AppRunner(app)

    # Configurar el bucle de eventos
    loop = asyncio.get_event_loop()
    await runner.setup()

    #site = web.TCPSite(runner, '0.0.0.0', puerto,ssl_context=ssl_context) ver este tema
    # Permitir conexiones en IPv4
    site_ipv4 = web.TCPSite(runner, '0.0.0.0', puerto,ssl_context=ssl_context)
    await site_ipv4.start()
    
    # Permitir conexiones en IPv6 si lo queremos que funcione se habilita
    #site_ipv6 = web.TCPSite(runner, '::', puerto, ssl_context=ssl_context)
    #await site_ipv6.start()

    print("Servidor web en ejecución en https://0.0.0.0:",puerto)

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        # Termina todos los workers correctamente
        await image_queue.put(None)  # Enviar señal de terminación al worker
        await runner.cleanup()
        await site_ipv4.stop()

        # Cierra el executor
        executor.shutdown(wait=True)
        # Limpiar el bucle de eventos
        #loop.run_until_complete(runner.cleanup())

        # Cerrar el bucle de eventos
        #loop.stop()
        #loop.run_until_complete(loop.shutdown_asyncgens())
        #loop.close()
        
        # Detener sitios IPv4 e IPv6
        #loop.run_until_complete(site_ipv4.stop())
        #loop.run_until_complete(site_ipv6.stop())
        
if __name__ == '__main__':
    # Ejecutar el servidor principal
    asyncio.run(main())