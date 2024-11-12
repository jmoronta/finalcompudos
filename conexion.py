import aiomysql
import aiofiles
from datetime import datetime

async def insert_en_tabla(imagen, patente, link):
    # Conexión asincrónica a la base de datos
    async with aiomysql.connect(
        host="localhost", 
        user="root",
        password="password",
        db="registros_patentes"
    ) as conexion:
        
        async with conexion.cursor() as cursor:
            # Obtener la fecha y hora actual
            fecha_hora_actual = datetime.now()

            # Leer la imagen de forma asincrónica
            async with aiofiles.open(imagen, 'rb') as f:
                imagen_data = await f.read()

            url = link 
            linkfull, linklat, linklon = url[0], url[1], url[2] 
            cadena = patente  # Reemplaza "Ejemplo de cadena" con tu cadena

            # Insertar los datos en la tabla de forma asincrónica
            consulta = """
                INSERT INTO patente(fecha_hora, imagen, ubicacion, patente, latitud, longitud) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            datos = (fecha_hora_actual, imagen_data, linkfull, cadena, linklat, linklon)
            await cursor.execute(consulta, datos)
            
            # Confirmar la operación de forma asincrónica
            await conexion.commit()


async def obtener_datos():
    try:
        # Conexión asincrónica a la base de datos
        async with aiomysql.connect(
            host="localhost",
            user="root",
            password="password",
            db="registros_patentes"
        ) as conexion:
            async with conexion.cursor() as cursor:
                # Ejecutar la consulta SELECT de forma asincrónica
                consulta = "SELECT * FROM patente"
                await cursor.execute(consulta)

                # Obtener todos los registros de forma asincrónica
                datos = await cursor.fetchall()
                return datos
    except aiomysql.MySQLError as e:
        print("Error al obtener datos de la tabla:", e)

        
        
async def insertar_cobro(patente, tiempo, monto):
    try:
        async with aiomysql.connect(
            host="localhost", 
            user="root",
            password="password",
            db="registros_patentes"
        ) as conexion:
            async with conexion.cursor() as cursor:
                consulta = "INSERT INTO cobros (patente, tiempo, cobrar) VALUES (%s, %s, %s)"
                datos = (patente, tiempo, monto)
                await cursor.execute(consulta, datos)

                # Confirmar la operación de forma asincrónica
                await conexion.commit()
    except aiomysql.MySQLError as e:
        print(f"Error al insertar en la tabla cobros: {e}")

        
async def dashboard_data():
    async with aiomysql.connect(
        host="localhost", 
        user="root",
        password="password",
        db="registros_patentes"
    ) as conexion:
        async with conexion.cursor() as cursor:
            # Contar la cantidad de patentes
            await cursor.execute("SELECT COUNT(*) FROM patente")
            cantidad_patentes = (await cursor.fetchone())[0]

            # Contar la cantidad de ubicaciones
            await cursor.execute("SELECT COUNT(DISTINCT ubicacion) FROM patente")
            cantidad_ubicaciones = (await cursor.fetchone())[0]

            # Sumar todos los cobros
            await cursor.execute("SELECT SUM(monto) FROM cobros")
            suma_cobros = (await cursor.fetchone())[0] or 0  # En caso de que no haya cobros, devolver 0

    # Preparar los datos como un objeto JSON
    data = {
        'cantidad_patentes': cantidad_patentes,
        'cantidad_ubicaciones': cantidad_ubicaciones,
        'suma_cobros': suma_cobros
    }

    return data


